import { executeCommand } from "./commands.js";
import { runInteractive } from "./interactive.js";

export async function runCli(argv) {
  if (!argv.length && process.stdin.isTTY) {
    await runInteractive(process.cwd());
    return;
  }

  const output = await executeCommand(argv, { cwd: process.cwd() });
  if (output) console.log(output);
}
