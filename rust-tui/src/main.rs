use std::{
    env,
    io::{self, BufRead, BufReader, BufWriter, Write},
    path::PathBuf,
    process::{Child, ChildStdin, Command as ProcessCommand, Stdio},
    sync::mpsc::{self, Receiver},
    thread,
    time::Duration,
};

use crossterm::{
    cursor::{SetCursorStyle, Show},
    event::{
        self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyEventKind, KeyModifiers,
        KeyboardEnhancementFlags, MouseEventKind, PopKeyboardEnhancementFlags,
        PushKeyboardEnhancementFlags,
    },
    execute,
    terminal::{self, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    Frame, Terminal,
    backend::CrosstermBackend,
    layout::{Alignment, Constraint, Direction, Layout, Position, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span, Text},
    widgets::{Block, Borders, Clear, Paragraph, Wrap},
};
use serde::Deserialize;
use unicode_width::{UnicodeWidthChar, UnicodeWidthStr};

const PIXEL_MARK: [&str; 11] = [
    "         BBAAAAAAB          ",
    "     BAWWWWWWWWWWWWWAAB     ",
    "   BWWWWWWWWWWWWWWWWWWWAB   ",
    "  AWWWWWWWAAB   BAAAAAAAAB  ",
    " AWWWWWWWA        BAAAAAAAB ",
    " AWWWWWWWB         BAAAAAAB ",
    " BWWWWWWWA         AAAAAAAB ",
    "  AWWWWWAABB    BBAAAAAAAB  ",
    "   BAAAAAAAAAAAAAAAAAAAAB   ",
    "      BAAAAAAAAAAAAAAB      ",
    "          BBBBBBBB          ",
];

#[derive(Clone)]
struct Command {
    name: String,
    description: String,
    source_backed: bool,
}

fn local_commands() -> Vec<Command> {
    [
        ("/help", "Show keyboard help"),
        ("/context", "Toggle project context view"),
        ("/changes", "Show saved artifact changes"),
        ("/new", "Save this conversation and start a new one"),
        ("/resume", "Resume the most recently saved conversation"),
        ("/exit", "Close the terminal interface"),
    ]
    .into_iter()
    .map(|(name, description)| Command {
        name: name.into(),
        description: description.into(),
        source_backed: false,
    })
    .collect()
}

#[derive(Deserialize)]
struct BridgeCommand {
    name: String,
    description: String,
}

#[derive(Clone, Deserialize)]
struct ConversationMessage {
    role: String,
    text: String,
}

#[derive(Clone, Deserialize)]
struct DiffRow {
    kind: String,
    #[serde(default)]
    old_line: Option<usize>,
    #[serde(default)]
    new_line: Option<usize>,
    text: String,
}

#[derive(Clone)]
struct Patch {
    path: String,
    status: String,
    added: usize,
    removed: usize,
    rows: Vec<DiffRow>,
    rows_truncated: bool,
    expanded: bool,
}

#[derive(Clone)]
enum TranscriptItem {
    Text(String),
    Patch(Patch),
}

impl Palette {
    fn terminal_default() -> Self {
        let no_color =
            env::var_os("NO_COLOR").is_some() || env::var("TERM").is_ok_and(|term| term == "dumb");
        Self {
            background: Color::Reset,
            surface: Color::Reset,
            text: Color::Reset,
            muted: Color::Reset,
            accent: Color::Reset,
            selected: if no_color {
                Color::Reset
            } else {
                Color::Rgb(56, 56, 56)
            },
            border: Color::Reset,
            added: if no_color { Color::Reset } else { Color::Green },
            removed: if no_color { Color::Reset } else { Color::Red },
            composer_surface: if no_color {
                Color::Reset
            } else {
                Color::Rgb(56, 56, 56)
            },
            composer_text: Color::Reset,
            status_model: if no_color {
                Color::Reset
            } else {
                Color::Rgb(218, 195, 145)
            },
            status_path: if no_color {
                Color::Reset
            } else {
                Color::Rgb(133, 190, 143)
            },
            status_attention: if no_color {
                Color::Reset
            } else {
                Color::Rgb(211, 177, 105)
            },
            ascii: env::var("OMNIX_ASCII").is_ok_and(|value| {
                matches!(value.to_ascii_lowercase().as_str(), "1" | "true" | "yes")
            }),
        }
    }
}

#[derive(Deserialize)]
struct BridgeEvent {
    version: u32,
    event: String,
    #[serde(default)]
    action: Option<String>,
    #[serde(default)]
    id: Option<String>,
    #[serde(default)]
    text: Option<String>,
    #[serde(default)]
    message: Option<String>,
    #[serde(default)]
    exit_code: Option<i32>,
    #[serde(default)]
    path: Option<String>,
    #[serde(default)]
    context: Option<String>,
    #[serde(default)]
    command: Option<String>,
    #[serde(default)]
    commands: Vec<BridgeCommand>,
    #[serde(default)]
    argv: Vec<String>,
    #[serde(default)]
    workspace: Option<String>,
    #[serde(default)]
    project: Option<String>,
    #[serde(default)]
    model: Option<String>,
    #[serde(default)]
    account_status: Option<String>,
    #[serde(default)]
    conversation: Vec<ConversationMessage>,
    #[serde(default)]
    status: Option<String>,
    #[serde(default)]
    added: usize,
    #[serde(default)]
    removed: usize,
    #[serde(default)]
    lines: Vec<DiffRow>,
    #[serde(default)]
    rows_truncated: bool,
}

struct EngineBridge {
    child: Child,
    input: BufWriter<ChildStdin>,
    events: Receiver<BridgeEvent>,
    next_id: u64,
    context: String,
    workspace: String,
    project: String,
    model: String,
    account_status: String,
    conversation: Vec<ConversationMessage>,
    commands: Vec<Command>,
}

impl EngineBridge {
    fn spawn(workspace: &PathBuf) -> io::Result<Self> {
        let source = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../ai-cli");
        let local_python = if cfg!(windows) {
            source.join(".venv/Scripts/python.exe")
        } else {
            source.join(".venv/bin/python")
        };
        let python = env::var_os("OMNIX_PYTHON")
            .map(PathBuf::from)
            .or_else(|| local_python.exists().then_some(local_python))
            .unwrap_or_else(|| PathBuf::from("python3"));
        let mut process = ProcessCommand::new(python);
        process
            .args(["-m", "omnix_cli.bridge", "--workspace"])
            .arg(workspace)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit());

        if let Ok(source) = source.canonicalize() {
            let mut python_path = source.into_os_string();
            if let Some(existing) = env::var_os("PYTHONPATH") {
                python_path.push(if cfg!(windows) { ";" } else { ":" });
                python_path.push(existing);
            }
            process.env("PYTHONPATH", python_path);
        }

        let mut child = process.spawn()?;
        let input = child.stdin.take().ok_or_else(|| {
            io::Error::other("Could not open the local Python bridge input stream.")
        })?;
        let output = child.stdout.take().ok_or_else(|| {
            io::Error::other("Could not open the local Python bridge output stream.")
        })?;
        let mut reader = BufReader::new(output);
        let mut hello = String::new();
        reader.read_line(&mut hello)?;
        let ready: BridgeEvent = serde_json::from_str(&hello).map_err(io::Error::other)?;
        if ready.version != 1 || ready.event != "ready" {
            return Err(io::Error::other(
                "The local Python bridge returned an invalid handshake.",
            ));
        }

        let (sender, events) = mpsc::channel();
        thread::spawn(move || {
            for line in reader.lines().map_while(Result::ok) {
                if let Ok(event) = serde_json::from_str::<BridgeEvent>(&line) {
                    if sender.send(event).is_err() {
                        break;
                    }
                }
            }
        });

        Ok(Self {
            child,
            input: BufWriter::new(input),
            events,
            next_id: 1,
            context: ready.context.unwrap_or_default(),
            workspace: ready
                .workspace
                .unwrap_or_else(|| workspace.display().to_string()),
            project: ready.project.unwrap_or_else(|| "workspace".into()),
            model: ready.model.unwrap_or_else(|| "no model selected".into()),
            account_status: ready.account_status.unwrap_or_else(|| "unknown".into()),
            conversation: ready.conversation,
            commands: ready
                .commands
                .into_iter()
                .map(|command| Command {
                    name: format!("/{}", command.name),
                    description: command.description,
                    source_backed: true,
                })
                .chain(
                    [
                        ("/help", "Show keyboard help"),
                        ("/context", "Toggle project context view"),
                        ("/changes", "Show saved artifact changes"),
                        ("/new", "Save this conversation and start a new one"),
                        ("/resume", "Resume the most recently saved conversation"),
                        ("/exit", "Close the terminal interface"),
                    ]
                    .into_iter()
                    .map(|(name, description)| Command {
                        name: name.into(),
                        description: description.into(),
                        source_backed: false,
                    }),
                )
                .collect(),
        })
    }

    fn run(&mut self, text: &str) -> io::Result<String> {
        let id = self.next_id.to_string();
        self.next_id += 1;
        let request_type = bridge_request_type(text);
        self.send(serde_json::json!({
            "version": 1,
            "type": request_type,
            "id": id,
            "input": text
        }))?;
        Ok(id)
    }

    fn cancel(&mut self, id: &str) -> io::Result<()> {
        self.send(serde_json::json!({"version": 1, "type": "cancel", "id": id}))
    }

    fn send(&mut self, request: serde_json::Value) -> io::Result<()> {
        serde_json::to_writer(&mut self.input, &request).map_err(io::Error::other)?;
        self.input.write_all(b"\n")?;
        self.input.flush()
    }
}

fn bridge_request_type(text: &str) -> &'static str {
    match text.trim() {
        "/new" => "session_new",
        "/resume" => "session_resume",
        _ => "run",
    }
}

impl Drop for EngineBridge {
    fn drop(&mut self) {
        let _ = self.send(serde_json::json!({"version": 1, "type": "shutdown"}));
        let _ = self.child.wait();
    }
}

struct Palette {
    background: Color,
    surface: Color,
    text: Color,
    muted: Color,
    accent: Color,
    selected: Color,
    border: Color,
    added: Color,
    removed: Color,
    composer_surface: Color,
    composer_text: Color,
    status_model: Color,
    status_path: Color,
    status_attention: Color,
    ascii: bool,
}

struct App {
    commands: Vec<Command>,
    input: String,
    cursor: usize,
    transcript: Vec<TranscriptItem>,
    running: bool,
    welcome: bool,
    notice: Option<String>,
    selected_command: usize,
    palette_offset: usize,
    previous_input: Option<String>,
    previous_cursor: usize,
    palette_open: bool,
    command_inserted: bool,
    context_open: bool,
    help_open: bool,
    transcript_scroll: u16,
    busy: bool,
    active_request: Option<String>,
    context_text: String,
    last_patches: Vec<Patch>,
    pending_handoff: Option<Vec<String>>,
    command_history: Vec<String>,
    history_index: Option<usize>,
    history_draft: String,
    focus: Focus,
    exit_armed: bool,
    workspace: String,
    project: String,
    model: String,
    account_status: String,
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Focus {
    Composer,
    Transcript,
    Context,
}

impl Default for App {
    fn default() -> Self {
        Self {
            commands: local_commands(),
            input: String::new(),
            cursor: 0,
            transcript: Vec::new(),
            running: true,
            welcome: true,
            notice: None,
            selected_command: 0,
            palette_offset: 0,
            previous_input: None,
            previous_cursor: 0,
            palette_open: false,
            command_inserted: false,
            context_open: false,
            help_open: false,
            transcript_scroll: 0,
            busy: false,
            active_request: None,
            context_text: String::new(),
            last_patches: Vec::new(),
            pending_handoff: None,
            command_history: Vec::new(),
            history_index: None,
            history_draft: String::new(),
            focus: Focus::Composer,
            exit_armed: false,
            workspace: env::current_dir()
                .map_or_else(|_| ".".into(), |path| path.display().to_string()),
            project: "workspace".into(),
            model: "no model selected".into(),
            account_status: "unknown".into(),
        }
    }
}

impl App {
    fn initialize(&mut self, bridge: &EngineBridge) {
        self.context_text = bridge.context.clone();
        self.commands = bridge.commands.clone();
        self.workspace = bridge.workspace.clone();
        self.project = bridge.project.clone();
        self.model = bridge.model.clone();
        self.account_status = bridge.account_status.clone();
        self.transcript
            .extend(bridge.conversation.iter().map(|message| {
                TranscriptItem::Text(format!(
                    "{}  {}",
                    if message.role == "user" {
                        "You"
                    } else {
                        "Master"
                    },
                    message.text
                ))
            }));
        self.welcome = self.transcript.is_empty();
        self.trim_transcript();
    }

    fn trim_transcript(&mut self) {
        const MAX_ITEMS: usize = 100;
        const MAX_CHARS: usize = 524_288;
        while self.transcript.len() > MAX_ITEMS {
            self.transcript.remove(0);
        }
        let item_size = |item: &TranscriptItem| match item {
            TranscriptItem::Text(text) => text.len(),
            TranscriptItem::Patch(patch) => {
                patch.path.len() + patch.rows.iter().map(|row| row.text.len()).sum::<usize>()
            }
        };
        let mut total = self.transcript.iter().map(item_size).sum::<usize>();
        while total > MAX_CHARS && self.transcript.len() > 1 {
            total = total.saturating_sub(item_size(&self.transcript.remove(0)));
        }
        if self.last_patches.len() > 25 {
            self.last_patches.drain(..self.last_patches.len() - 25);
        }
    }

    fn submit(&mut self) -> Option<String> {
        if self.palette_open {
            if let Some(command) =
                filtered_commands(&self.input, &self.commands).get(self.selected_command)
            {
                self.input = format!("{} ", command.name);
                self.cursor = self.input.len();
                self.palette_open = false;
                self.command_inserted = true;
                return None;
            }
            self.notice = Some("No matching action. Clear the filter or press Escape.".into());
            return None;
        }
        if self.busy {
            self.notice = Some("Wait for the current command to finish.".into());
            return None;
        }
        let input = self.input.trim().to_owned();
        if input.is_empty() {
            return None;
        }
        if input != "/exit" && input != "/help" && input != "/context" && input != "/changes" {
            if self.command_history.last() != Some(&input) {
                self.command_history.push(input.clone());
            }
            self.history_index = None;
        }
        if input == "/exit" {
            self.input.clear();
            self.cursor = 0;
            self.running = false;
        } else if input == "/help" {
            self.input.clear();
            self.cursor = 0;
            self.help_open = true;
        } else if input == "/context" {
            self.input.clear();
            self.cursor = 0;
            self.context_open = !self.context_open;
            self.focus = if self.context_open {
                Focus::Context
            } else {
                Focus::Composer
            };
            self.notice = Some(
                if self.context_open {
                    "Workspace context opened."
                } else {
                    "Workspace context closed."
                }
                .into(),
            );
        } else if input == "/changes" {
            self.input.clear();
            self.cursor = 0;
            if self.last_patches.is_empty() {
                self.notice = Some("No generated artifact changes in this session.".into());
            } else {
                self.transcript
                    .extend(self.last_patches.iter().cloned().map(TranscriptItem::Patch));
                self.notice = Some("Showing saved generated artifact changes.".into());
            }
        } else if input.starts_with('/') && !input.starts_with("//") {
            self.transcript
                .push(TranscriptItem::Text(format!("Running {input}")));
            self.notice = Some("Command running…".into());
            self.input.clear();
            self.cursor = 0;
            self.busy = true;
            self.welcome = false;
            self.command_inserted = false;
            return Some(input);
        } else {
            let message = if input.starts_with("//") {
                &input[1..]
            } else {
                input.as_str()
            };
            self.transcript
                .push(TranscriptItem::Text(format!("You  {message}")));
            self.transcript.push(TranscriptItem::Text(String::new()));
            self.transcript.push(TranscriptItem::Text("Master".into()));
            self.notice = Some("Sending to Master Agent…".into());
            self.input.clear();
            self.cursor = 0;
            self.busy = true;
            self.welcome = false;
            self.command_inserted = false;
            return Some(input);
        }
        self.command_inserted = false;
        self.welcome = false;
        None
    }

    fn handle_key(&mut self, code: KeyCode, modifiers: KeyModifiers) -> Option<String> {
        if !(code == KeyCode::Char('c') && modifiers == KeyModifiers::CONTROL) {
            self.exit_armed = false;
        }
        if self.help_open {
            if matches!(code, KeyCode::Esc | KeyCode::Enter) {
                self.help_open = false;
            }
            return None;
        }

        match (code, modifiers) {
            (KeyCode::Char('?'), KeyModifiers::SHIFT | KeyModifiers::NONE)
                if self.input.is_empty() && self.focus == Focus::Composer =>
            {
                self.help_open = true;
                self.welcome = false;
            }
            (KeyCode::Char('c'), KeyModifiers::CONTROL) if self.busy => {
                self.notice = Some("Interrupt requested…".into());
            }
            (KeyCode::Char('c'), KeyModifiers::CONTROL) => {
                if self.exit_armed {
                    self.running = false;
                } else {
                    self.exit_armed = true;
                    self.notice =
                        Some("Press Ctrl+C again to exit; your conversation is saved.".into());
                }
            }
            (KeyCode::Char('d'), KeyModifiers::CONTROL) if self.input.is_empty() => {
                self.running = false;
            }
            (KeyCode::Tab, _) if !self.palette_open => {
                self.focus = match self.focus {
                    Focus::Composer => Focus::Transcript,
                    Focus::Transcript if self.context_open => Focus::Context,
                    Focus::Transcript | Focus::Context => Focus::Composer,
                };
            }
            (KeyCode::BackTab, _) | (KeyCode::Tab, KeyModifiers::SHIFT) => {
                self.focus = match self.focus {
                    Focus::Composer if self.context_open => Focus::Context,
                    Focus::Composer | Focus::Transcript => Focus::Transcript,
                    Focus::Context => Focus::Transcript,
                };
            }
            (KeyCode::Char(' '), _) if self.focus == Focus::Transcript => {
                if let Some(TranscriptItem::Patch(patch)) = self
                    .transcript
                    .iter_mut()
                    .rev()
                    .find(|item| matches!(item, TranscriptItem::Patch(_)))
                {
                    patch.expanded = !patch.expanded;
                }
            }
            (KeyCode::Char('j'), KeyModifiers::CONTROL) if self.focus == Focus::Composer => {
                self.exit_armed = false;
                self.input.insert(self.cursor, '\n');
                self.cursor += 1;
                self.welcome = false;
            }
            (KeyCode::Enter, KeyModifiers::SHIFT) if self.focus == Focus::Composer => {
                self.exit_armed = false;
                self.input.insert(self.cursor, '\n');
                self.cursor += 1;
                self.welcome = false;
                self.after_edit();
            }
            (KeyCode::Tab, _) if self.palette_open => self.insert_selected_command(),
            (KeyCode::Up, _) if self.palette_open => {
                self.selected_command = self.selected_command.saturating_sub(1);
                self.keep_selection_visible();
            }
            (KeyCode::Down, _) if self.palette_open => {
                let last = filtered_commands(&self.input, &self.commands)
                    .len()
                    .saturating_sub(1);
                self.selected_command = (self.selected_command + 1).min(last);
                self.keep_selection_visible();
            }
            (KeyCode::Up, _)
                if !self.palette_open && self.focus == Focus::Composer && self.input.is_empty() =>
            {
                self.transcript_scroll = self.transcript_scroll.saturating_add(1)
            }
            (KeyCode::Down, _)
                if !self.palette_open && self.focus == Focus::Composer && self.input.is_empty() =>
            {
                self.transcript_scroll = self.transcript_scroll.saturating_sub(1)
            }
            (KeyCode::Up, _) if !self.palette_open && self.focus == Focus::Composer => {
                self.move_cursor_vertical(true)
            }
            (KeyCode::Down, _) if !self.palette_open && self.focus == Focus::Composer => {
                self.move_cursor_vertical(false)
            }
            (KeyCode::Char('p'), KeyModifiers::CONTROL) if self.focus == Focus::Composer => {
                self.history_up()
            }
            (KeyCode::Char('n'), KeyModifiers::CONTROL) if self.focus == Focus::Composer => {
                self.history_down()
            }
            (KeyCode::PageUp, _) => {
                self.transcript_scroll = self.transcript_scroll.saturating_add(8);
            }
            (KeyCode::PageDown, _) => {
                self.transcript_scroll = self.transcript_scroll.saturating_sub(8);
            }
            (KeyCode::Enter, _) => return self.submit(),
            (KeyCode::Esc, _) if self.palette_open => self.close_palette(),
            (KeyCode::Esc, _) if self.context_open => {
                self.context_open = false;
                self.focus = Focus::Composer;
                self.notice = None;
            }
            (KeyCode::Esc, _) if self.focus != Focus::Composer => self.focus = Focus::Composer,
            (KeyCode::Esc, _) => self.notice = Some("Draft kept.".into()),
            (KeyCode::Left, _) if self.focus == Focus::Composer => {
                self.cursor = self.previous_char_boundary(self.cursor)
            }
            (KeyCode::Right, _) if self.focus == Focus::Composer => {
                self.cursor = self.next_char_boundary(self.cursor)
            }
            (KeyCode::Home, _) if self.focus == Focus::Composer => {
                self.cursor = self.input[..self.cursor].rfind('\n').map_or(0, |i| i + 1)
            }
            (KeyCode::End, _) if self.focus == Focus::Composer => {
                self.cursor = self.input[self.cursor..]
                    .find('\n')
                    .map_or(self.input.len(), |i| self.cursor + i)
            }
            (KeyCode::Backspace, _) if self.focus == Focus::Composer => {
                if self.cursor > 0 {
                    let start = self.previous_char_boundary(self.cursor);
                    self.input.drain(start..self.cursor);
                    self.cursor = start;
                }
                self.after_edit();
            }
            (KeyCode::Delete, _) if self.focus == Focus::Composer => {
                if self.cursor < self.input.len() {
                    let end = self.next_char_boundary(self.cursor);
                    self.input.drain(self.cursor..end);
                }
                self.after_edit();
            }
            (KeyCode::Char(ch), KeyModifiers::NONE | KeyModifiers::SHIFT)
                if self.focus == Focus::Composer =>
            {
                if ch == '/' && self.input.is_empty() && self.cursor == 0 {
                    self.previous_input = Some(self.input.clone());
                    self.previous_cursor = self.cursor;
                    self.palette_open = true;
                }
                self.input.insert(self.cursor, ch);
                self.cursor += ch.len_utf8();
                if self.palette_open {
                    self.selected_command = 0;
                    self.palette_offset = 0;
                }
                self.after_edit();
            }
            _ => {}
        }
        None
    }

    fn receive(&mut self, event: BridgeEvent) {
        let Some(active_id) = self.active_request.as_deref() else {
            return;
        };
        if event.id.as_deref().is_some_and(|id| id != active_id) {
            return;
        }
        match event.event.as_str() {
            "session" => {
                let action = event.action.as_deref().unwrap_or_default();
                self.transcript = event
                    .conversation
                    .into_iter()
                    .map(|message| {
                        TranscriptItem::Text(format!(
                            "{}  {}",
                            if message.role == "user" {
                                "You"
                            } else {
                                "Master"
                            },
                            message.text
                        ))
                    })
                    .collect();
                self.welcome = action == "new";
                self.transcript_scroll = 0;
                self.last_patches.clear();
                self.busy = false;
                self.active_request = None;
                self.notice = event.message;
            }
            "started" => {
                self.notice = Some(format!("Running {}…", event.command.unwrap_or_default()));
            }
            "output" => {
                let text = clean_terminal_text(&event.text.unwrap_or_default());
                if !text.is_empty() {
                    self.welcome = false;
                    self.transcript.push(TranscriptItem::Text(text));
                }
            }
            "patch" => {
                let patch = Patch {
                    path: event.path.unwrap_or_else(|| ".project/artifacts".into()),
                    status: event.status.unwrap_or_else(|| "saved".into()),
                    added: event.added,
                    removed: event.removed,
                    rows: event.lines,
                    rows_truncated: event.rows_truncated,
                    expanded: true,
                };
                self.last_patches.push(patch.clone());
                self.transcript.push(TranscriptItem::Patch(patch));
            }
            "context" => {
                self.context_text = event.context.unwrap_or_default();
                self.project = event.project.unwrap_or_else(|| self.project.clone());
                self.model = event.model.unwrap_or_else(|| self.model.clone());
            }
            "handoff" => {
                self.pending_handoff = Some(event.argv);
                self.busy = false;
                self.active_request = None;
                self.notice =
                    Some("Switching to the native terminal for interactive approval…".into());
            }
            "complete" => {
                let code = event.exit_code.unwrap_or_default();
                self.transcript.push(TranscriptItem::Text(if code == 0 {
                    "Finished successfully.".into()
                } else {
                    format!("Command exited with status {code}.")
                }));
                self.busy = false;
                self.active_request = None;
                self.notice = None;
            }
            "cancelled" => self.notice = Some("Command interrupted.".into()),
            "error" => {
                self.transcript.push(TranscriptItem::Text(format!(
                    "Error · {}",
                    event.message.unwrap_or_default()
                )));
                self.busy = false;
                self.active_request = None;
                self.notice = Some("The request could not be completed.".into());
            }
            _ => {}
        }
        self.trim_transcript();
    }

    fn after_edit(&mut self) {
        self.welcome = false;
        self.command_inserted = false;
        self.history_index = None;
        let draft = self.input.trim_end();
        if self.palette_open && (!draft.starts_with('/') || draft.starts_with("//")) {
            self.palette_open = false;
            self.previous_input = None;
            self.selected_command = 0;
            self.palette_offset = 0;
            return;
        }
        if self.palette_open
            && self
                .commands
                .iter()
                .any(|command| draft.starts_with(&format!("{} ", command.name)))
        {
            self.palette_open = false;
        }
        self.selected_command = 0;
        self.palette_offset = 0;
        self.keep_selection_visible();
    }

    fn insert_selected_command(&mut self) {
        if let Some(command) =
            filtered_commands(&self.input, &self.commands).get(self.selected_command)
        {
            self.input = format!("{} ", command.name);
            self.cursor = self.input.len();
            self.palette_open = false;
            self.command_inserted = true;
        }
    }

    fn close_palette(&mut self) {
        self.input = self.previous_input.take().unwrap_or_default();
        self.cursor = self.previous_cursor.min(self.input.len());
        self.palette_open = false;
        self.selected_command = 0;
        self.palette_offset = 0;
    }

    fn keep_selection_visible(&mut self) {
        let terminal_rows = terminal::size().map_or(24, |(_, rows)| rows);
        let body_rows = terminal_rows.saturating_sub(10).min(24) as usize;
        let visible_rows = body_rows.saturating_sub(2).max(1);
        if self.selected_command < self.palette_offset {
            self.palette_offset = self.selected_command;
        } else if self.selected_command >= self.palette_offset + visible_rows {
            self.palette_offset = self.selected_command + 1 - visible_rows;
        }
    }

    fn previous_char_boundary(&self, at: usize) -> usize {
        self.input[..at]
            .char_indices()
            .next_back()
            .map_or(0, |(index, _)| index)
    }

    fn next_char_boundary(&self, at: usize) -> usize {
        self.input[at..]
            .char_indices()
            .nth(1)
            .map_or(self.input.len(), |(index, _)| at + index)
    }

    fn paste(&mut self, text: &str) {
        if self.input.is_empty() && text.starts_with('/') {
            self.previous_input = Some(String::new());
            self.previous_cursor = self.cursor;
            self.palette_open = true;
        }
        self.input.insert_str(self.cursor, text);
        self.cursor += text.len();
        if self.palette_open {
            self.selected_command = 0;
            self.palette_offset = 0;
        }
        self.after_edit();
    }

    fn history_up(&mut self) {
        if self.command_history.is_empty() {
            return;
        }
        let index = match self.history_index {
            Some(index) => index.saturating_sub(1),
            None => {
                self.history_draft = self.input.clone();
                self.command_history.len() - 1
            }
        };
        self.history_index = Some(index);
        self.input = self.command_history[index].clone();
        self.cursor = self.input.len();
    }

    fn history_down(&mut self) {
        let Some(index) = self.history_index else {
            return;
        };
        if index + 1 < self.command_history.len() {
            let next = index + 1;
            self.history_index = Some(next);
            self.input = self.command_history[next].clone();
        } else {
            self.history_index = None;
            self.input = std::mem::take(&mut self.history_draft);
        }
        self.cursor = self.input.len();
    }

    fn move_cursor_vertical(&mut self, upward: bool) {
        let line_start = self.input[..self.cursor]
            .rfind('\n')
            .map_or(0, |index| index + 1);
        let column = self.input[line_start..self.cursor].chars().count();
        let target = if upward {
            if line_start == 0 {
                return;
            }
            let previous_end = line_start - 1;
            let previous_start = self.input[..previous_end]
                .rfind('\n')
                .map_or(0, |index| index + 1);
            let previous_line = &self.input[previous_start..previous_end];
            previous_start
                + previous_line
                    .char_indices()
                    .nth(column)
                    .map_or(previous_line.len(), |(index, _)| index)
        } else {
            let current_end = self.input[self.cursor..]
                .find('\n')
                .map_or(self.input.len(), |index| self.cursor + index);
            if current_end == self.input.len() {
                return;
            }
            let next_start = current_end + 1;
            let next_end = self.input[next_start..]
                .find('\n')
                .map_or(self.input.len(), |index| next_start + index);
            let next_line = &self.input[next_start..next_end];
            next_start
                + next_line
                    .char_indices()
                    .nth(column)
                    .map_or(next_line.len(), |(index, _)| index)
        };
        self.cursor = target;
    }
}

struct TerminalSession {
    active: bool,
}

impl TerminalSession {
    fn enter() -> io::Result<Self> {
        terminal::enable_raw_mode()?;
        if let Err(error) = execute!(
            io::stdout(),
            EnterAlternateScreen,
            EnableMouseCapture,
            PushKeyboardEnhancementFlags(
                KeyboardEnhancementFlags::DISAMBIGUATE_ESCAPE_CODES
                    | KeyboardEnhancementFlags::REPORT_EVENT_TYPES,
            ),
            SetCursorStyle::BlinkingBlock
        ) {
            let _ = terminal::disable_raw_mode();
            return Err(error);
        }
        Ok(Self { active: true })
    }

    fn suspend(&mut self) -> io::Result<()> {
        if self.active {
            execute!(
                io::stdout(),
                SetCursorStyle::DefaultUserShape,
                Show,
                DisableMouseCapture,
                PopKeyboardEnhancementFlags,
                LeaveAlternateScreen
            )?;
            terminal::disable_raw_mode()?;
            self.active = false;
        }
        Ok(())
    }

    fn resume(&mut self) -> io::Result<()> {
        if !self.active {
            terminal::enable_raw_mode()?;
            if let Err(error) = execute!(
                io::stdout(),
                EnterAlternateScreen,
                EnableMouseCapture,
                PushKeyboardEnhancementFlags(
                    KeyboardEnhancementFlags::DISAMBIGUATE_ESCAPE_CODES
                        | KeyboardEnhancementFlags::REPORT_EVENT_TYPES,
                ),
                SetCursorStyle::BlinkingBlock
            ) {
                let _ = terminal::disable_raw_mode();
                return Err(error);
            }
            self.active = true;
        }
        Ok(())
    }
}

impl Drop for TerminalSession {
    fn drop(&mut self) {
        let _ = self.suspend();
    }
}

fn main() -> io::Result<()> {
    let Some((workspace, plain)) = parse_args()? else {
        return Ok(());
    };
    if plain {
        return run_plain(workspace);
    }
    let bridge = EngineBridge::spawn(&workspace);
    let mut session = TerminalSession::enter()?;
    let backend = CrosstermBackend::new(io::stdout());
    let mut terminal = Terminal::new(backend)?;
    let mut app = App::default();
    let mut bridge = match bridge {
        Ok(bridge) => {
            app.initialize(&bridge);
            Some(bridge)
        }
        Err(error) => {
            app.notice = Some(format!("Engine bridge unavailable: {error}"));
            None
        }
    };
    terminal.draw(|frame| draw(frame, &app))?;

    while app.running {
        let mut redraw = false;
        if event::poll(Duration::from_millis(60))? {
            match event::read()? {
                Event::Key(key) if key.kind == KeyEventKind::Press => {
                    let is_cancel = key.code == KeyCode::Char('c')
                        && key.modifiers == KeyModifiers::CONTROL
                        && app.busy;
                    if is_cancel {
                        if let (Some(bridge), Some(id)) = (&mut bridge, &app.active_request) {
                            let _ = bridge.cancel(id);
                        }
                    }
                    if let Some(input) = app.handle_key(key.code, key.modifiers) {
                        if let Some(bridge) = &mut bridge {
                            match bridge.run(&input) {
                                Ok(id) => app.active_request = Some(id),
                                Err(error) => {
                                    app.busy = false;
                                    app.transcript.push(TranscriptItem::Text(format!(
                                        "Could not start request · {error}"
                                    )));
                                }
                            }
                        } else {
                            app.busy = false;
                            app.transcript.push(TranscriptItem::Text(
                                "No Python engine is available; the request was not sent.".into(),
                            ));
                        }
                    }
                    redraw = true;
                }
                Event::Paste(text) => {
                    app.paste(&text);
                    redraw = true;
                }
                Event::Mouse(mouse) => {
                    match (mouse.kind, app.palette_open) {
                        (MouseEventKind::ScrollUp, true) => {
                            app.selected_command = app.selected_command.saturating_sub(1);
                            app.keep_selection_visible();
                        }
                        (MouseEventKind::ScrollDown, true) => {
                            let last = filtered_commands(&app.input, &app.commands)
                                .len()
                                .saturating_sub(1);
                            app.selected_command = (app.selected_command + 1).min(last);
                            app.keep_selection_visible();
                        }
                        (MouseEventKind::ScrollUp, false) => {
                            app.transcript_scroll = app.transcript_scroll.saturating_add(3);
                        }
                        (MouseEventKind::ScrollDown, false) => {
                            app.transcript_scroll = app.transcript_scroll.saturating_sub(3);
                        }
                        _ => continue,
                    }
                    redraw = true;
                }
                Event::Resize(_, _) => redraw = true,
                _ => continue,
            }
        }
        if let Some(bridge) = &bridge {
            while let Ok(event) = bridge.events.try_recv() {
                app.receive(event);
                redraw = true;
            }
        }
        if let Some(argv) = app.pending_handoff.take() {
            session.suspend()?;
            let result = argv
                .split_first()
                .ok_or_else(|| io::Error::other("The bridge returned an empty command."))
                .and_then(|(program, args)| {
                    ProcessCommand::new(program)
                        .args(args)
                        .current_dir(&workspace)
                        .status()
                });
            session.resume()?;
            terminal.clear()?;
            match result {
                Ok(status) if status.success() => {
                    app.transcript
                        .push(TranscriptItem::Text("Interactive command finished.".into()));
                    app.notice = None;
                }
                Ok(status) => {
                    app.transcript.push(TranscriptItem::Text(format!(
                        "Interactive command exited with status {}.",
                        status.code().unwrap_or(1)
                    )));
                    app.notice = Some("Interactive command did not complete successfully.".into());
                }
                Err(error) => {
                    app.transcript.push(TranscriptItem::Text(format!(
                        "Could not start interactive command · {error}"
                    )));
                    app.notice = Some("Interactive command could not be started.".into());
                }
            }
            redraw = true;
        }
        if redraw {
            terminal.draw(|frame| draw(frame, &app))?;
        }
    }
    Ok(())
}

fn parse_args() -> io::Result<Option<(PathBuf, bool)>> {
    let mut args = env::args_os().skip(1);
    let mut workspace = env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
    let mut plain = env::var("TERM").is_ok_and(|term| term == "dumb");
    while let Some(arg) = args.next() {
        if arg == "--help" || arg == "-h" {
            println!(
                "Omnix terminal frontend\n\nUsage: omnix-tui [--workspace PATH] [--plain]\n\nOptions:\n  -w, --workspace PATH  Project workspace (defaults to the current directory)\n  --plain               Use linear, unstyled output\n  -h, --help            Show this help"
            );
            return Ok(None);
        }
        if arg == "--plain" {
            plain = true;
            continue;
        }
        if arg == "--workspace" || arg == "-w" {
            workspace = args.next().map(PathBuf::from).ok_or_else(|| {
                io::Error::new(io::ErrorKind::InvalidInput, "--workspace requires a path")
            })?;
            continue;
        }
        if let Some(value) = arg
            .to_str()
            .and_then(|arg| arg.strip_prefix("--workspace="))
        {
            workspace = PathBuf::from(value);
            continue;
        }
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            format!("Unknown argument: {}", arg.to_string_lossy()),
        ));
    }
    workspace = workspace.canonicalize()?;
    if !workspace.is_dir() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "The workspace path must be a directory.",
        ));
    }
    Ok(Some((workspace, plain)))
}

fn run_plain(workspace: PathBuf) -> io::Result<()> {
    let mut bridge = EngineBridge::spawn(&workspace)?;
    let mut patches = Vec::new();
    println!("Omnix CLI · {}", workspace.display());
    println!("Type a goal for Master, / for commands, or /exit to leave.");
    let stdin = io::stdin();
    loop {
        print!("> ");
        io::stdout().flush()?;
        let mut input = String::new();
        if stdin.read_line(&mut input)? == 0 {
            break;
        }
        let input = input.trim().to_owned();
        if input.is_empty() {
            continue;
        }
        match input.as_str() {
            "/exit" => break,
            "/" => {
                for command in &bridge.commands {
                    println!("{:<24} {}", command.name, command.description);
                }
                continue;
            }
            "/help" => {
                println!("Enter sends a message or runs a command. Prefix / for CLI commands.");
                println!(
                    "Use / to list commands, /context for project context, /changes for the last patch."
                );
                continue;
            }
            "/context" => {
                println!("{}", bridge.context);
                continue;
            }
            "/changes" => {
                if patches.is_empty() {
                    println!("No generated artifact changes in this session.");
                } else {
                    for patch in &patches {
                        println!("{patch}");
                    }
                }
                continue;
            }
            _ => {}
        }

        let request_id = bridge.run(&input)?;
        if input.starts_with('/') {
            println!("Running {input}");
        } else {
            println!("You  {input}\n\nMaster");
        }
        io::stdout().flush()?;
        loop {
            let event = bridge
                .events
                .recv()
                .map_err(|_| io::Error::other("The Python engine bridge closed unexpectedly."))?;
            if event.id.as_deref().is_some_and(|id| id != request_id) {
                continue;
            }
            match event.event.as_str() {
                "started" => {}
                "output" => {
                    print!("{}", clean_terminal_text(&event.text.unwrap_or_default()));
                    io::stdout().flush()?;
                }
                "patch" => {
                    let heading = format!(
                        "Saved generated artifact changes · {}",
                        event.path.unwrap_or_default()
                    );
                    let diff = clean_terminal_text(&event.text.unwrap_or_default());
                    let patch = format!(
                        "{heading}\n{diff}\nGenerated content saved locally; application source was not applied."
                    );
                    println!("{patch}");
                    patches.push(patch);
                }
                "context" => bridge.context = event.context.unwrap_or_default(),
                "handoff" => {
                    let status = run_handoff(&event.argv, &workspace)?;
                    println!(
                        "Interactive command exited with status {}.",
                        status.code().unwrap_or(1)
                    );
                    break;
                }
                "complete" => {
                    println!(
                        "\nCommand exited with status {}.",
                        event.exit_code.unwrap_or_default()
                    );
                    break;
                }
                "error" => {
                    println!("\nError · {}", event.message.unwrap_or_default());
                    break;
                }
                _ => {}
            }
        }
    }
    Ok(())
}

fn run_handoff(argv: &[String], workspace: &PathBuf) -> io::Result<std::process::ExitStatus> {
    let (program, args) = argv
        .split_first()
        .ok_or_else(|| io::Error::other("The bridge returned an empty command."))?;
    ProcessCommand::new(program)
        .args(args)
        .current_dir(workspace)
        .status()
}

fn clean_terminal_text(text: &str) -> String {
    let mut cleaned = String::with_capacity(text.len());
    let mut chars = text.chars().peekable();
    while let Some(ch) = chars.next() {
        if ch == '\u{1b}' {
            match chars.next() {
                Some('[') => {
                    for sequence_char in chars.by_ref() {
                        if ('@'..='~').contains(&sequence_char) {
                            break;
                        }
                    }
                }
                Some(']') => {
                    let mut previous_escape = false;
                    for sequence_char in chars.by_ref() {
                        if sequence_char == '\u{7}' || previous_escape && sequence_char == '\\' {
                            break;
                        }
                        previous_escape = sequence_char == '\u{1b}';
                    }
                }
                _ => {}
            }
        } else if ch == '\n' || ch == '\t' || !ch.is_control() {
            cleaned.push(ch);
        }
    }
    cleaned
}

fn draw(frame: &mut Frame<'_>, app: &App) {
    let palette = Palette::terminal_default();
    let area = frame.area();
    frame.render_widget(
        Block::default().style(Style::default().bg(palette.background).fg(palette.text)),
        area,
    );

    let composer_height = (3 + app.input.matches('\n').count() as u16).min(6);
    let header_height = if area.height < 22 { 1 } else { 2 };
    let [header, body, activity, composer, footer] = Layout::default()
        .direction(Direction::Vertical)
        .margin(1)
        .constraints([
            Constraint::Length(header_height),
            Constraint::Min(6),
            Constraint::Length(1),
            Constraint::Length(composer_height),
            Constraint::Length(2),
        ])
        .areas(area);

    draw_header(frame, header, app, &palette);
    draw_body(frame, body, app, &palette);
    draw_activity(frame, activity, app, &palette);
    draw_composer(frame, composer, app, &palette);
    draw_footer(frame, footer, app, &palette);
    if app.help_open {
        draw_help(frame, area, &palette);
    }

    let before_cursor = &app.input[..app.cursor];
    let cursor_line = before_cursor.matches('\n').count();
    let line_start = before_cursor.rfind('\n').map_or(0, |index| index + 1);
    let columns = composer.width.saturating_sub(2).max(1) as usize;
    let prompt_width = if app.input.is_empty() { 0 } else { 2 };
    let cell_column = prompt_width + UnicodeWidthStr::width(&before_cursor[line_start..]);
    let wrapped_rows = cell_column / columns;
    let cursor_column = cell_column % columns;
    let cursor_row = before_cursor
        .split('\n')
        .take(cursor_line)
        .map(|line| {
            (prompt_width + UnicodeWidthStr::width(line))
                .div_ceil(columns)
                .max(1)
        })
        .sum::<usize>()
        + wrapped_rows;
    let cursor_x = composer.x.saturating_add(1 + cursor_column as u16);
    let cursor_y = composer.y.saturating_add(1 + cursor_row as u16);
    if app.focus == Focus::Composer
        && cursor_x < composer.right().saturating_sub(1)
        && cursor_y < composer.bottom().saturating_sub(1)
    {
        frame.set_cursor_position(Position::new(cursor_x, cursor_y));
    }
}

fn draw_header(frame: &mut Frame<'_>, area: Rect, app: &App, palette: &Palette) {
    let first = Line::from(vec![
        Span::styled("›_ ", Style::default().fg(palette.accent)),
        Span::styled(
            "Omnix CLI",
            Style::default()
                .fg(palette.text)
                .add_modifier(Modifier::BOLD),
        ),
        Span::styled(
            format!(" (v{})", env!("CARGO_PKG_VERSION")),
            Style::default().fg(palette.muted),
        ),
    ]);
    let second = if app.welcome {
        Line::from(Span::styled(
            truncate_cells(&display_path(&app.workspace), area.width as usize),
            Style::default().fg(palette.muted),
        ))
    } else {
        Line::from("")
    };
    frame.render_widget(Paragraph::new(vec![first, second]), area);
}

fn display_path(path: &str) -> String {
    let home = env::var("HOME").or_else(|_| env::var("USERPROFILE")).ok();
    home.as_deref()
        .filter(|home| path == *home || path.starts_with(&format!("{home}/")))
        .map_or_else(
            || path.to_owned(),
            |home| format!("~{}", &path[home.len()..]),
        )
}

fn draw_activity(frame: &mut Frame<'_>, area: Rect, app: &App, palette: &Palette) {
    let status = app.notice.as_deref().or_else(|| {
        if app.busy {
            Some("Working · Ctrl+C to interrupt")
        } else if !app.welcome {
            Some("Ready")
        } else {
            None
        }
    });
    if let Some(status) = status {
        frame.render_widget(
            Paragraph::new(truncate_cells(status, area.width as usize))
                .alignment(Alignment::Right)
                .style(Style::default().fg(if app.busy || app.notice.is_some() {
                    palette.status_attention
                } else {
                    palette.muted
                })),
            area,
        );
    }
}

fn draw_body(frame: &mut Frame<'_>, area: Rect, app: &App, palette: &Palette) {
    if app.palette_open {
        draw_command_palette(
            frame,
            area,
            &app.input,
            &app.commands,
            app.selected_command,
            app.palette_offset,
            palette,
        );
    } else {
        if app.welcome {
            draw_welcome(frame, area, app, palette);
        } else {
            let mut lines = Vec::new();
            for item in &app.transcript {
                match item {
                    TranscriptItem::Text(message) => {
                        lines.extend(message.lines().map(Line::from));
                        lines.push(Line::from(""));
                    }
                    TranscriptItem::Patch(patch) => lines.extend(patch_lines(patch, palette)),
                }
            }
            let bottom = lines.len().saturating_sub(area.height as usize);
            let scroll = bottom
                .saturating_sub(app.transcript_scroll as usize)
                .min(u16::MAX as usize) as u16;
            frame.render_widget(
                Paragraph::new(lines)
                    .style(Style::default().fg(palette.text))
                    .scroll((scroll, 0))
                    .wrap(Wrap { trim: false }),
                area,
            );
        }
        if app.context_open {
            draw_context(frame, area, app, palette);
        }
    }
}

fn patch_lines(patch: &Patch, palette: &Palette) -> Vec<Line<'static>> {
    let state = if patch.status == "saved" {
        "Saved artifact"
    } else {
        "Generation failed"
    };
    let marker = if patch.expanded { "▾" } else { "▸" };
    let mut lines = vec![Line::from(vec![
        Span::styled(
            format!("{marker} {state}  "),
            Style::default()
                .fg(palette.text)
                .add_modifier(Modifier::BOLD),
        ),
        Span::styled(patch.path.clone(), Style::default().fg(palette.muted)),
        Span::styled(
            format!("  +{} −{}", patch.added, patch.removed),
            Style::default().fg(palette.text),
        ),
    ])];
    if patch.expanded {
        let gutter = |old: Option<usize>, new: Option<usize>| {
            format!(
                "{:>4} {:>4} │ ",
                old.map_or(String::new(), |n| n.to_string()),
                new.map_or(String::new(), |n| n.to_string())
            )
        };
        for row in &patch.rows {
            let (prefix, style) = match row.kind.as_str() {
                "added" => ("+", Style::default().fg(palette.added)),
                "removed" => ("−", Style::default().fg(palette.removed)),
                "hunk" => ("@", Style::default().fg(palette.muted)),
                _ => (" ", Style::default().fg(palette.text)),
            };
            let text = if row.kind == "hunk" {
                row.text.clone()
            } else {
                format!(
                    "{}{}{}",
                    gutter(row.old_line, row.new_line),
                    prefix,
                    row.text
                )
            };
            lines.push(Line::from(Span::styled(text, style)));
        }
        if patch.rows_truncated {
            lines.push(Line::from(Span::styled(
                "Additional diff rows omitted from this view.",
                Style::default().fg(palette.muted),
            )));
        }
        lines.push(Line::from(Span::styled(
            "Generated artifact only; application source was not modified.",
            Style::default().fg(palette.muted),
        )));
    } else {
        lines.push(Line::from(Span::styled(
            "Space to expand · generated artifact change",
            Style::default().fg(palette.muted),
        )));
    }
    lines.push(Line::from(""));
    lines
}

fn draw_welcome(frame: &mut Frame<'_>, area: Rect, app: &App, palette: &Palette) {
    let account_line = match app.account_status.as_str() {
        "connected" => "Omnix account connected · /status for details",
        "disconnected" => "Omnix account not connected · /login to sign in",
        _ => "Account status unavailable · /status to check",
    };
    let next_step =
        if app.model == "Unconfigured" || app.model == "Local" || app.model.contains("unset") {
            "Type a goal · / commands · /config to set a model"
        } else {
            "Type a goal, or / to browse commands."
        };
    if area.height < PIXEL_MARK.len() as u16 + 3 {
        if area.height >= PIXEL_MARK.len() as u16 {
            let height = PIXEL_MARK.len() as u16;
            let logo_area = Rect {
                x: area.x,
                y: area.y + area.height.saturating_sub(height) / 2,
                width: area.width,
                height,
            };
            frame.render_widget(
                Paragraph::new(Text::from_iter(pixel_mark_lines(palette)))
                    .alignment(Alignment::Center),
                logo_area,
            );
            if area.height > height {
                let status = Rect {
                    x: area.x,
                    y: area.bottom().saturating_sub(1),
                    width: area.width,
                    height: 1,
                };
                frame.render_widget(
                    Paragraph::new(account_line)
                        .alignment(Alignment::Center)
                        .style(
                            Style::default().fg(if app.account_status == "disconnected" {
                                palette.status_attention
                            } else {
                                palette.muted
                            }),
                        ),
                    status,
                );
            }
            return;
        }
        let lines = vec![
            Line::from(Span::styled(
                "Omnix CLI",
                Style::default()
                    .fg(palette.text)
                    .add_modifier(Modifier::BOLD),
            )),
            Line::from(Span::styled(
                "One conversation. An AI engineering team behind it.",
                Style::default().fg(palette.muted),
            )),
            Line::from(Span::styled(
                account_line,
                Style::default().fg(palette.muted),
            )),
        ];
        let height = lines.len() as u16;
        let compact = Rect {
            x: area.x,
            y: area.y + area.height.saturating_sub(height) / 2,
            width: area.width,
            height,
        };
        frame.render_widget(
            Paragraph::new(lines)
                .alignment(Alignment::Center)
                .wrap(Wrap { trim: true }),
            compact,
        );
        return;
    }
    let logo_height = PIXEL_MARK.len() as u16;
    let total = logo_height.saturating_add(4);
    let top = area.y.saturating_add(area.height.saturating_sub(total) / 2);
    let logo_area = Rect {
        x: area.x,
        y: top,
        width: area.width,
        height: logo_height,
    };

    frame.render_widget(
        Paragraph::new(Text::from_iter(pixel_mark_lines(palette))).alignment(Alignment::Center),
        logo_area,
    );

    let copy_area = Rect {
        x: area.x,
        y: logo_area.bottom().saturating_add(1),
        width: area.width,
        height: 3,
    };
    frame.render_widget(
        Paragraph::new(vec![
            Line::from(Span::styled(
                "One conversation. An AI engineering team behind it.",
                Style::default()
                    .fg(palette.text)
                    .add_modifier(Modifier::BOLD),
            )),
            Line::from(Span::styled(
                account_line,
                Style::default().fg(if app.account_status == "disconnected" {
                    palette.status_attention
                } else {
                    palette.muted
                }),
            )),
            Line::from(Span::styled(next_step, Style::default().fg(palette.muted))),
        ])
        .alignment(Alignment::Center),
        copy_area,
    );
}

fn pixel_mark_lines(palette: &Palette) -> Vec<Line<'static>> {
    PIXEL_MARK
        .iter()
        .map(|row| {
            Line::from(
                row.chars()
                    .map(|pixel| {
                        let color = match pixel {
                            'W' => palette.text,
                            'A' => palette.accent,
                            'B' => palette.muted,
                            _ => palette.background,
                        };
                        let glyph = match (pixel, palette.ascii) {
                            ('W', true) => "#",
                            ('A', true) => "+",
                            ('B', true) => ".",
                            ('W', false) => "█",
                            ('A', false) => "▓",
                            ('B', false) => "▒",
                            _ => " ",
                        };
                        Span::styled(glyph.to_owned(), Style::default().fg(color))
                    })
                    .collect::<Vec<_>>(),
            )
        })
        .collect()
}

fn draw_command_palette(
    frame: &mut Frame<'_>,
    area: Rect,
    query: &str,
    commands: &[Command],
    selected: usize,
    offset: usize,
    palette: &Palette,
) {
    let filtered = filtered_commands(query, commands);
    if area.height < 2 || area.width < 12 {
        return;
    }
    let empty = filtered.is_empty();
    let content_rows = if empty {
        2
    } else {
        filtered
            .len()
            .min(8)
            .min(area.height.saturating_sub(2) as usize)
    };
    let panel_height = (content_rows as u16 + 2).min(area.height);
    let panel = Rect {
        x: area.x,
        y: area.bottom().saturating_sub(panel_height),
        width: area.width,
        height: panel_height,
    };
    let visible_count = filtered.len().min(panel.height.saturating_sub(2) as usize);
    let width = panel.width;
    let inner_width = width as usize;
    let command_width = filtered
        .iter()
        .map(|command| UnicodeWidthStr::width(command.name.as_str()))
        .max()
        .unwrap_or(12)
        .clamp(12, 22)
        .min(inner_width / 2);
    let show_source = inner_width >= command_width + 42;
    let source_width = if show_source { 5 } else { 0 };
    let description_width = inner_width.saturating_sub(command_width + source_width + 4);
    frame.render_widget(Clear, panel);
    let first = offset.min(filtered.len());
    let last = (first + visible_count).min(filtered.len());
    let header = if empty {
        format!(
            "Commands · no matches · {} CLI actions",
            commands
                .iter()
                .filter(|command| command.source_backed)
                .count()
        )
    } else {
        format!(
            "Commands · {}–{last} of {}  / filter",
            first + 1,
            filtered.len()
        )
    };
    let mut lines = vec![Line::from(Span::styled(
        truncate_cells(&header, inner_width),
        Style::default()
            .fg(palette.muted)
            .add_modifier(Modifier::DIM),
    ))];
    if empty {
        lines.push(Line::from(Span::styled(
            truncate_cells("No matching actions · remove / or press Esc", inner_width),
            Style::default().fg(palette.muted),
        )));
    }
    lines.extend(
        filtered[first..last]
            .iter()
            .enumerate()
            .map(|(row, command)| {
                let index = first + row;
                let selected_row = index == selected;
                let row_style = if selected_row {
                    let style = Style::default()
                        .bg(palette.selected)
                        .fg(palette.text)
                        .add_modifier(Modifier::BOLD);
                    if palette.selected == Color::Reset {
                        style.add_modifier(Modifier::REVERSED)
                    } else {
                        style
                    }
                } else {
                    Style::default().fg(palette.text)
                };
                let marker = if selected_row { "› " } else { "  " };
                let name = truncate_cells(&command.name, command_width);
                let padding = command_width.saturating_sub(UnicodeWidthStr::width(name.as_str()));
                let description = truncate_cells(&command.description, description_width);
                let detail_style = if selected_row {
                    row_style
                } else {
                    Style::default()
                        .fg(palette.muted)
                        .add_modifier(Modifier::DIM)
                };
                let name_style = if selected_row {
                    row_style.add_modifier(Modifier::BOLD)
                } else {
                    row_style
                };
                let mut spans = vec![
                    Span::styled(
                        format!("{marker}{name}{}  ", " ".repeat(padding)),
                        name_style,
                    ),
                    Span::styled(description, detail_style),
                ];
                if show_source {
                    spans.push(Span::styled(
                        if command.source_backed {
                            "  CLI"
                        } else {
                            "  UI"
                        },
                        detail_style,
                    ));
                }
                Line::from(spans)
            }),
    );
    let footer = if area.width < 56 {
        "↑↓ move · Enter/Tab insert · Esc close"
    } else {
        "↑↓ Move · Enter / Tab insert · Esc restore draft"
    };
    if panel.height > 1 {
        lines.push(Line::from(Span::styled(
            truncate_cells(footer, inner_width),
            Style::default()
                .fg(palette.muted)
                .add_modifier(Modifier::DIM),
        )));
    }
    frame.render_widget(Paragraph::new(lines), panel);
}

fn truncate_cells(text: &str, max_width: usize) -> String {
    if UnicodeWidthStr::width(text) <= max_width {
        return text.to_owned();
    }
    if max_width == 0 {
        return String::new();
    }
    let target = max_width.saturating_sub(1);
    let mut result = String::new();
    for character in text.chars() {
        if UnicodeWidthStr::width(result.as_str()) + UnicodeWidthChar::width(character).unwrap_or(0)
            > target
        {
            break;
        }
        result.push(character);
    }
    result.push('…');
    result
}

fn draw_context(frame: &mut Frame<'_>, area: Rect, app: &App, palette: &Palette) {
    let width = area.width.min(48);
    let context = Rect {
        x: area.right().saturating_sub(width),
        y: area.y,
        width,
        height: area.height,
    };
    frame.render_widget(Clear, context);
    let mut lines = vec![
        Line::from(Span::styled(
            "Workspace",
            Style::default()
                .fg(palette.accent)
                .add_modifier(Modifier::BOLD),
        )),
        Line::from(app.workspace.as_str()),
    ];
    if !app.context_text.is_empty() {
        lines.push(Line::from(""));
        lines.extend(app.context_text.lines().map(Line::from));
    }
    frame.render_widget(
        Paragraph::new(lines)
            .block(
                Block::default()
                    .title(" Context ")
                    .borders(Borders::ALL)
                    .border_style(Style::default().fg(if app.focus == Focus::Context {
                        palette.accent
                    } else {
                        palette.border
                    }))
                    .style(Style::default().bg(palette.surface).fg(palette.text)),
            )
            .wrap(Wrap { trim: true }),
        context,
    );
}

fn draw_help(frame: &mut Frame<'_>, area: Rect, palette: &Palette) {
    let width = area.width.min(72);
    let height = area.height.min(12);
    let popup = Rect {
        x: area.x + area.width.saturating_sub(width) / 2,
        y: area.y + area.height.saturating_sub(height) / 2,
        width,
        height,
    };
    frame.render_widget(Clear, popup);
    let lines = vec![
        Line::from("Enter           Insert selected action / run command or send message"),
        Line::from(
            "Up / Down       Move through results; scroll transcript when composer is empty",
        ),
        Line::from("Ctrl+P / Ctrl+N  Browse command history"),
        Line::from("Tab             Insert selected command"),
        Line::from("Tab / Shift+Tab Move focus; Space toggles a focused change"),
        Line::from("Shift+Return    Add a new line to the draft"),
        Line::from("?               Open this shortcuts panel"),
        Line::from("Escape          Close palette or context"),
        Line::from("Ctrl+C          Interrupt; twice at idle exits. Ctrl+D exits on empty draft."),
        Line::from(""),
        Line::from("Commands execute through the local Python engine."),
    ];
    frame.render_widget(
        Paragraph::new(lines)
            .block(
                Block::default()
                    .title(" Keyboard help ")
                    .borders(Borders::ALL)
                    .border_style(Style::default().fg(palette.border))
                    .style(Style::default().bg(palette.surface).fg(palette.text)),
            )
            .wrap(Wrap { trim: true }),
        popup,
    );
}

fn draw_composer(frame: &mut Frame<'_>, area: Rect, app: &App, palette: &Palette) {
    let lines = if app.input.is_empty() {
        vec![Line::from(vec![Span::styled(
            "Ask Omnix anything",
            Style::default().fg(palette.composer_text),
        )])]
    } else {
        app.input
            .split('\n')
            .enumerate()
            .map(|(index, text)| {
                let marker = if index == 0 { "> " } else { "  " };
                Line::from(vec![
                    Span::styled(marker, Style::default().fg(palette.composer_text)),
                    Span::styled(text, Style::default().fg(palette.composer_text)),
                ])
            })
            .collect()
    };
    let focused = app.focus == Focus::Composer;
    frame.render_widget(
        Block::default().style(Style::default().bg(if focused {
            palette.composer_surface
        } else {
            palette.surface
        })),
        area,
    );
    let content = Rect {
        x: area.x.saturating_add(1),
        y: area.y.saturating_add(1),
        width: area.width.saturating_sub(2),
        height: area.height.saturating_sub(1),
    };
    frame.render_widget(
        Paragraph::new(lines)
            .style(Style::default().fg(if focused {
                palette.composer_text
            } else {
                palette.text
            }))
            .wrap(Wrap { trim: false }),
        content,
    );
}

fn filtered_commands<'a>(query: &str, commands: &'a [Command]) -> Vec<&'a Command> {
    let term = query
        .trim_start_matches('/')
        .split_whitespace()
        .next()
        .unwrap_or_default()
        .to_lowercase();
    if term.is_empty() {
        return commands.iter().collect();
    }

    let mut matches = commands
        .iter()
        .enumerate()
        .filter_map(|(index, command)| {
            let name = command.name.trim_start_matches('/').to_lowercase();
            let description = command.description.to_lowercase();
            let rank = if name == term {
                (0, 0)
            } else if name.starts_with(&term) {
                (1, name.len().saturating_sub(term.len()))
            } else if let Some(gaps) = subsequence_gap_score(&name, &term) {
                (2, gaps)
            } else if let Some(position) = description.find(&term) {
                (3, position)
            } else {
                return None;
            };
            Some((rank, index, command))
        })
        .collect::<Vec<_>>();
    matches.sort_by_key(|(rank, index, _)| (*rank, *index));
    matches.into_iter().map(|(_, _, command)| command).collect()
}

fn subsequence_gap_score(candidate: &str, query: &str) -> Option<usize> {
    let candidate = candidate.chars().collect::<Vec<_>>();
    let query = query.chars().collect::<Vec<_>>();
    let mut search_from = 0;
    let mut previous = None;
    let mut gaps = 0;

    for target in query {
        let relative = candidate[search_from..]
            .iter()
            .position(|character| *character == target)?;
        let position = search_from + relative;
        if let Some(previous) = previous {
            gaps += position.saturating_sub(previous + 1);
        }
        previous = Some(position);
        search_from = position + 1;
    }

    Some(gaps)
}

fn draw_footer(frame: &mut Frame<'_>, area: Rect, app: &App, palette: &Palette) {
    let context = if app.welcome {
        app.project.clone()
    } else {
        display_path(&app.workspace)
    };
    let separator = " · ";
    let full_width = UnicodeWidthStr::width(app.model.as_str())
        + UnicodeWidthStr::width(separator)
        + UnicodeWidthStr::width(context.as_str());
    let details = if full_width <= area.width as usize {
        Line::from(vec![
            Span::styled(app.model.clone(), Style::default().fg(palette.status_model)),
            Span::styled(separator, Style::default().fg(palette.muted)),
            Span::styled(context, Style::default().fg(palette.status_path)),
        ])
    } else {
        Line::from(Span::styled(
            truncate_cells(
                &format!("{}{}{}", app.model, separator, context),
                area.width as usize,
            ),
            Style::default().fg(palette.status_path),
        ))
    };
    let hints = if app.palette_open {
        "↑↓ move · Enter/Tab insert · Esc close"
    } else if area.width < 68 {
        "Enter send · Shift+Return newline · / commands · ? shortcuts"
    } else {
        "Enter send · Shift+Return newline · / commands · ? shortcuts · Tab/Shift+Tab focus"
    };
    let hints = truncate_cells(hints, area.width as usize);
    let [details_row, hints_row] = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Length(1), Constraint::Length(1)])
        .areas(area);
    frame.render_widget(Paragraph::new(details), details_row);
    frame.render_widget(
        Paragraph::new(hints).style(Style::default().fg(palette.muted)),
        hints_row,
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shift_return_adds_a_line_without_submitting() {
        let mut app = App::default();
        app.focus = Focus::Composer;

        assert_eq!(app.handle_key(KeyCode::Enter, KeyModifiers::SHIFT), None);
        assert_eq!(app.input, "\n");
        assert!(!app.busy);
    }

    #[test]
    fn arrow_keys_scroll_an_empty_composer_not_input_history() {
        let mut app = App::default();
        app.focus = Focus::Composer;
        app.command_history.push("previous message".into());

        app.handle_key(KeyCode::Up, KeyModifiers::NONE);

        assert_eq!(app.transcript_scroll, 1);
        assert!(app.input.is_empty());
        assert_eq!(app.history_index, None);
    }

    #[test]
    fn new_and_resume_are_local_session_requests() {
        assert_eq!(bridge_request_type(" /new "), "session_new");
        assert_eq!(bridge_request_type("/resume"), "session_resume");
        assert_eq!(bridge_request_type("/logout"), "run");
    }
}
