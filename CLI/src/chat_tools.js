import path from "node:path";
import { loadMemory, saveMemory } from "./brain.js";
import { nowIso, omnixPath, slugify, timestampId, writeJson, writeText } from "./files.js";

export async function newChat(cwd, title = "") {
  const chat = await loadMemory(cwd, "chat");
  const id = `chat-${timestampId()}`;
  const session = {
    id,
    title: title || "Untitled chat",
    created_at: nowIso(),
    updated_at: nowIso(),
    messages: []
  };
  chat.sessions = chat.sessions || [];
  chat.sessions.push(session);
  chat.current_session_id = id;
  await saveMemory(cwd, "chat", chat);
  return `New chat started: ${session.title} (${id})`;
}

export async function renameChat(cwd, title) {
  if (!title) throw new Error("Usage: /rename <title>");
  const chat = await loadMemory(cwd, "chat");
  const session = currentSession(chat);
  session.title = title;
  session.updated_at = nowIso();
  await saveMemory(cwd, "chat", chat);
  return `Renamed current chat to: ${title}`;
}

export async function chatHistory(cwd) {
  const chat = await loadMemory(cwd, "chat");
  const sessions = chat.sessions || [];
  if (!sessions.length) return "No chat sessions yet. Run /new <title>.";
  return sessions
    .slice()
    .reverse()
    .map((session) => `${session.id}${session.id === chat.current_session_id ? " *" : ""}  ${session.title}  ${session.updated_at}`)
    .join("\n");
}

export async function reviewChat(cwd, id = "") {
  const chat = await loadMemory(cwd, "chat");
  const session = findSession(chat, id) || currentSession(chat, false);
  if (!session) return "No chat session found.";
  return [
    `Chat: ${session.title}`,
    `ID: ${session.id}`,
    `Created: ${session.created_at}`,
    `Updated: ${session.updated_at}`,
    `Messages: ${session.messages?.length || 0}`,
    "",
    ...(session.messages?.length ? session.messages.slice(-12).map((message) => `${message.role}: ${message.content}`) : ["No messages recorded yet."])
  ].join("\n");
}

export async function deleteChat(cwd, id = "", confirmed = false) {
  if (!confirmed) return "Chat not deleted. Re-run with --yes to confirm.";
  const chat = await loadMemory(cwd, "chat");
  const target = id && id !== "--yes" ? id : chat.current_session_id;
  const before = chat.sessions?.length || 0;
  chat.sessions = (chat.sessions || []).filter((session) => session.id !== target);
  if (chat.current_session_id === target) chat.current_session_id = chat.sessions.at(-1)?.id || null;
  await saveMemory(cwd, "chat", chat);
  return before === chat.sessions.length ? `No chat found for ${target}.` : `Deleted chat ${target}.`;
}

export async function exportChat(cwd, format = "md") {
  const chat = await loadMemory(cwd, "chat");
  const session = currentSession(chat, false);
  if (!session) return "No current chat to export.";
  const safeTitle = slugify(session.title, "chat");
  const extension = format === "json" ? "json" : "md";
  const target = omnixPath(cwd, "logs", "chats", `${safeTitle}-${session.id}.${extension}`);
  if (extension === "json") {
    await writeJson(target, session);
  } else {
    const body = [
      `# ${session.title}`,
      "",
      `- ID: ${session.id}`,
      `- Created: ${session.created_at}`,
      `- Updated: ${session.updated_at}`,
      "",
      ...(session.messages || []).map((message) => `## ${message.role}\n\n${message.content}\n`)
    ].join("\n");
    await writeText(target, body);
  }
  return `Exported chat to ${path.relative(cwd, target)}`;
}

export async function clearVisibleChat() {
  return "Visible terminal output cleared.";
}

export async function recordChatMessage(cwd, role, content) {
  const chat = await loadMemory(cwd, "chat");
  const session = currentSession(chat, true);
  session.messages = session.messages || [];
  session.messages.push({ role, content, at: nowIso() });
  session.updated_at = nowIso();
  await saveMemory(cwd, "chat", chat);
}

function currentSession(chat, create = true) {
  chat.sessions = chat.sessions || [];
  let session = findSession(chat, chat.current_session_id);
  if (!session && create) {
    session = {
      id: `chat-${timestampId()}`,
      title: "Untitled chat",
      created_at: nowIso(),
      updated_at: nowIso(),
      messages: []
    };
    chat.sessions.push(session);
    chat.current_session_id = session.id;
  }
  return session;
}

function findSession(chat, id) {
  if (!id) return null;
  return (chat.sessions || []).find((session) => session.id === id);
}
