use std::{io, time::Duration};

use crossterm::{
    cursor::{SetCursorStyle, Show},
    event::{self, Event, KeyCode, KeyEventKind, KeyModifiers},
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
use unicode_width::UnicodeWidthStr;

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

const UI_COMMANDS: [(&str, &str); 3] = [
    ("/help", "Show keyboard help"),
    ("/theme", "Switch black, blue or white appearance"),
    ("/exit", "Close the Rust frontend prototype"),
];

#[derive(Clone, Copy, PartialEq, Eq)]
enum Theme {
    Black,
    Blue,
    White,
}

impl Theme {
    fn parse(value: &str) -> Option<Self> {
        match value {
            "black" => Some(Self::Black),
            "blue" => Some(Self::Blue),
            "white" | "light" => Some(Self::White),
            _ => None,
        }
    }

    fn colors(self) -> Palette {
        match self {
            Self::Black => Palette {
                background: Color::Rgb(0, 0, 0),
                surface: Color::Rgb(17, 17, 17),
                text: Color::Rgb(242, 242, 242),
                muted: Color::Rgb(166, 166, 166),
                accent: Color::Rgb(228, 228, 231),
                selected: Color::Rgb(48, 48, 48),
                border: Color::Rgb(58, 58, 58),
            },
            Self::Blue => Palette {
                background: Color::Rgb(24, 35, 51),
                surface: Color::Rgb(34, 50, 70),
                text: Color::Rgb(234, 241, 252),
                muted: Color::Rgb(178, 194, 216),
                accent: Color::Rgb(166, 200, 255),
                selected: Color::Rgb(48, 76, 117),
                border: Color::Rgb(81, 103, 127),
            },
            Self::White => Palette {
                background: Color::Rgb(238, 242, 247),
                surface: Color::Rgb(220, 229, 239),
                text: Color::Rgb(23, 39, 61),
                muted: Color::Rgb(67, 89, 117),
                accent: Color::Rgb(37, 89, 173),
                selected: Color::Rgb(37, 89, 173),
                border: Color::Rgb(145, 160, 179),
            },
        }
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
}

struct App {
    input: String,
    transcript: Vec<String>,
    theme: Theme,
    running: bool,
    notice: Option<String>,
    selected_command: usize,
}

impl Default for App {
    fn default() -> Self {
        Self {
            input: String::new(),
            transcript: Vec::new(),
            theme: Theme::Black,
            running: true,
            notice: None,
            selected_command: 0,
        }
    }
}

impl App {
    fn submit(&mut self) {
        let input = self.input.trim().to_owned();
        self.input.clear();
        if input.is_empty() {
            return;
        }
        if input == "/exit" {
            self.running = false;
        } else if input == "/help" {
            self.notice = Some(
                "Enter submits · Ctrl+J inserts a newline · / opens UI commands · Ctrl+C exits"
                    .into(),
            );
        } else if let Some(theme) = input.strip_prefix("/theme ").and_then(Theme::parse) {
            self.theme = theme;
            self.notice = Some("Theme changed for this session.".into());
        } else if input == "/theme" {
            self.notice = Some("Use /theme black, /theme blue or /theme white.".into());
        } else if input.starts_with('/') {
            self.notice = Some("This prototype exposes only its local UI commands.".into());
        } else {
            self.transcript.push(format!("Not sent · {input}"));
            self.notice =
                Some("Engine bridge is not connected yet; this message was not sent.".into());
        }
    }

    fn handle_key(&mut self, code: KeyCode, modifiers: KeyModifiers) {
        match (code, modifiers) {
            (KeyCode::Char('c'), KeyModifiers::CONTROL) => self.running = false,
            (KeyCode::Char('j'), KeyModifiers::CONTROL) => self.input.push('\n'),
            (KeyCode::Tab, _) if self.input.starts_with('/') => {
                if let Some((command, _)) =
                    filtered_commands(&self.input).get(self.selected_command)
                {
                    self.input = format!("{command} ");
                }
            }
            (KeyCode::Up, _) if self.input.starts_with('/') => {
                self.selected_command = self.selected_command.saturating_sub(1);
            }
            (KeyCode::Down, _) if self.input.starts_with('/') => {
                let last = filtered_commands(&self.input).len().saturating_sub(1);
                self.selected_command = (self.selected_command + 1).min(last);
            }
            (KeyCode::Enter, _) => self.submit(),
            (KeyCode::Backspace, _) => {
                self.input.pop();
            }
            (KeyCode::Char(ch), KeyModifiers::NONE | KeyModifiers::SHIFT) => {
                self.input.push(ch);
                self.selected_command = 0;
            }
            _ => {}
        }
    }
}

struct TerminalSession;

impl TerminalSession {
    fn enter() -> io::Result<Self> {
        terminal::enable_raw_mode()?;
        if let Err(error) = execute!(
            io::stdout(),
            EnterAlternateScreen,
            SetCursorStyle::BlinkingBlock
        ) {
            let _ = terminal::disable_raw_mode();
            return Err(error);
        }
        Ok(Self)
    }
}

impl Drop for TerminalSession {
    fn drop(&mut self) {
        let _ = execute!(
            io::stdout(),
            SetCursorStyle::DefaultUserShape,
            Show,
            LeaveAlternateScreen
        );
        let _ = terminal::disable_raw_mode();
    }
}

fn main() -> io::Result<()> {
    let _session = TerminalSession::enter()?;
    let backend = CrosstermBackend::new(io::stdout());
    let mut terminal = Terminal::new(backend)?;
    let mut app = App::default();

    while app.running {
        terminal.draw(|frame| draw(frame, &app))?;
        if event::poll(Duration::from_millis(100))? {
            if let Event::Key(key) = event::read()? {
                if key.kind == KeyEventKind::Press {
                    app.handle_key(key.code, key.modifiers);
                }
            }
        }
    }
    Ok(())
}

fn draw(frame: &mut Frame<'_>, app: &App) {
    let palette = app.theme.colors();
    let area = frame.area();
    frame.render_widget(
        Block::default().style(Style::default().bg(palette.background).fg(palette.text)),
        area,
    );

    let composer_height = (4 + app.input.matches('\n').count() as u16).min(7);
    let [header, body, composer, footer] = Layout::default()
        .direction(Direction::Vertical)
        .margin(1)
        .constraints([
            Constraint::Length(2),
            Constraint::Min(8),
            Constraint::Length(composer_height),
            Constraint::Length(1),
        ])
        .areas(area);

    draw_header(frame, header, &palette);
    draw_body(frame, body, app, &palette);
    draw_composer(frame, composer, app, &palette);
    draw_footer(frame, footer, app, &palette);

    let wrap_width = composer.width.saturating_sub(4).max(1) as usize;
    let segments: Vec<&str> = app.input.split('\n').collect();
    let mut cursor_row = 0usize;
    for segment in segments.iter().take(segments.len().saturating_sub(1)) {
        let width = 2 + UnicodeWidthStr::width(*segment);
        cursor_row += width.div_ceil(wrap_width).max(1);
    }
    let last_segment = segments.last().copied().unwrap_or_default();
    let last_width = 2 + UnicodeWidthStr::width(last_segment);
    cursor_row += last_width / wrap_width;
    let cursor_column = last_width % wrap_width;
    let cursor_x = composer.x.saturating_add(1 + cursor_column as u16);
    let cursor_y = composer.y.saturating_add(1 + cursor_row as u16);
    if cursor_x < composer.right().saturating_sub(1)
        && cursor_y < composer.bottom().saturating_sub(1)
    {
        frame.set_cursor_position(Position::new(cursor_x, cursor_y));
    }
}

fn draw_header(frame: &mut Frame<'_>, area: Rect, palette: &Palette) {
    let brand = Line::from(vec![
        Span::styled(
            " OMNIX ",
            Style::default()
                .fg(palette.text)
                .add_modifier(Modifier::BOLD),
        ),
        Span::styled("·", Style::default().fg(palette.muted)),
        Span::styled(
            " Rust terminal preview ",
            Style::default().fg(palette.muted),
        ),
    ]);
    frame.render_widget(Paragraph::new(brand), area);
}

fn draw_body(frame: &mut Frame<'_>, area: Rect, app: &App, palette: &Palette) {
    if app.transcript.is_empty() && app.input.is_empty() {
        draw_welcome(frame, area, palette);
    } else {
        let lines = app
            .transcript
            .iter()
            .flat_map(|message| [Line::from(message.as_str()), Line::from("")])
            .collect::<Vec<_>>();
        frame.render_widget(
            Paragraph::new(lines)
                .style(Style::default().fg(palette.text))
                .wrap(Wrap { trim: false }),
            area,
        );
    }

    if app.input.starts_with('/') {
        draw_command_palette(frame, area, &app.input, app.selected_command, palette);
    }

    if let Some(notice) = &app.notice {
        let notice_area = Rect {
            x: area.x.saturating_add(2),
            y: area.bottom().saturating_sub(2),
            width: area.width.saturating_sub(4),
            height: 1,
        };
        frame.render_widget(
            Paragraph::new(notice.as_str()).style(Style::default().fg(palette.muted)),
            notice_area,
        );
    }
}

fn draw_welcome(frame: &mut Frame<'_>, area: Rect, palette: &Palette) {
    let logo_height = PIXEL_MARK.len() as u16;
    let total = logo_height.saturating_add(4);
    let top = area.y.saturating_add(area.height.saturating_sub(total) / 2);
    let logo_area = Rect {
        x: area.x,
        y: top,
        width: area.width,
        height: logo_height,
    };

    let logo_lines = PIXEL_MARK.iter().map(|row| {
        Line::from(
            row.chars()
                .map(|pixel| {
                    let color = match pixel {
                        'W' => palette.text,
                        'A' => palette.accent,
                        'B' => palette.muted,
                        _ => palette.background,
                    };
                    Span::styled(
                        if pixel == ' ' { " " } else { "█" },
                        Style::default().fg(color),
                    )
                })
                .collect::<Vec<_>>(),
        )
    });
    frame.render_widget(
        Paragraph::new(Text::from_iter(logo_lines)).alignment(Alignment::Center),
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
                "Type a goal, or / to begin.",
                Style::default().fg(palette.muted),
            )),
        ])
        .alignment(Alignment::Center),
        copy_area,
    );
}

fn draw_command_palette(
    frame: &mut Frame<'_>,
    area: Rect,
    query: &str,
    selected: usize,
    palette: &Palette,
) {
    let filtered = filtered_commands(query);
    if filtered.is_empty() {
        return;
    }

    let height = (filtered.len() as u16 + 2).min(area.height.saturating_sub(4));
    let width = area.width.min(60);
    let popup = Rect {
        x: area.x.saturating_add(2),
        y: area.bottom().saturating_sub(height + 1),
        width,
        height,
    };
    frame.render_widget(Clear, popup);
    let lines = filtered
        .iter()
        .enumerate()
        .map(|(index, (command, description))| {
            let marker = if index == selected { "› " } else { "  " };
            let row_style = if index == selected {
                Style::default()
                    .bg(palette.selected)
                    .fg(palette.text)
                    .add_modifier(Modifier::BOLD)
            } else {
                Style::default().bg(palette.surface)
            };
            Line::from(vec![
                Span::styled(marker, row_style.fg(palette.accent)),
                Span::styled(format!("{command:<10}"), row_style.fg(palette.accent)),
                Span::styled(*description, row_style.fg(palette.muted)),
            ])
        })
        .collect::<Vec<_>>();
    frame.render_widget(
        Paragraph::new(lines)
            .block(
                Block::default()
                    .title(" Local UI commands ")
                    .borders(Borders::ALL)
                    .border_style(Style::default().fg(palette.border))
                    .style(Style::default().bg(palette.surface).fg(palette.text)),
            )
            .style(Style::default().bg(palette.surface).fg(palette.text)),
        popup,
    );
}

fn draw_composer(frame: &mut Frame<'_>, area: Rect, app: &App, palette: &Palette) {
    let lines = if app.input.is_empty() {
        vec![Line::from(vec![
            Span::styled("> ", Style::default().fg(palette.accent)),
            Span::styled(
                "Describe what you want to work on",
                Style::default().fg(palette.muted),
            ),
        ])]
    } else {
        app.input
            .split('\n')
            .enumerate()
            .map(|(index, text)| {
                let marker = if index == 0 { "> " } else { "  " };
                Line::from(vec![
                    Span::styled(marker, Style::default().fg(palette.accent)),
                    Span::styled(text, Style::default().fg(palette.text)),
                ])
            })
            .collect()
    };
    frame.render_widget(
        Paragraph::new(lines)
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .border_style(Style::default().fg(palette.border))
                    .style(Style::default().bg(palette.surface).fg(palette.text)),
            )
            .wrap(Wrap { trim: false }),
        area,
    );
}

fn filtered_commands(query: &str) -> Vec<(&'static str, &'static str)> {
    let term = query.trim_start_matches('/').to_lowercase();
    UI_COMMANDS
        .iter()
        .copied()
        .filter(|(command, description)| {
            term.is_empty()
                || command.trim_start_matches('/').contains(&term)
                || description.to_lowercase().contains(&term)
        })
        .collect()
}

fn draw_footer(frame: &mut Frame<'_>, area: Rect, app: &App, palette: &Palette) {
    let theme = match app.theme {
        Theme::Black => "BLACK",
        Theme::Blue => "BLUE",
        Theme::White => "WHITE",
    };
    frame.render_widget(
        Paragraph::new(Line::from(vec![
            Span::styled("/ commands", Style::default().fg(palette.accent)),
            Span::styled(
                "   ·   Enter send   ·   Ctrl+C exit",
                Style::default().fg(palette.muted),
            ),
            Span::styled(
                format!("   ·   {theme}"),
                Style::default().fg(palette.muted),
            ),
        ])),
        area,
    );
}
