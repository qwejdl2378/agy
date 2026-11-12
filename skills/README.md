# agy skills

Copy a skill folder to `~/.gemini/config/skills/` (agy discovers `SKILL.md` there).

| Skill | What it does | Needs |
|---|---|---|
| `swiftui-snapshot` | Renders a SwiftUI root view to light/dark PNGs without an Xcode project so the agent can look at its own UI and fix it (max 3 rounds). | macOS, Xcode command-line tools |
| `compose-snapshot` | Builds Compose sources into a throwaway host app, installs it on a connected device/emulator and screenshots light/dark/landscape/font-scale. Only installs/updates its own package; never changes device settings or taps system dialogs. | Android SDK, Gradle 8.13, one device |

Both exist because "look at the result" is the single biggest UI-quality lever for agy: Gemini's vision is strong, but it only helps if the agent actually renders and inspects its output.
