# calendarz

A meeting alert widget for the [end-4/dots-hyprland](https://github.com/end-4/dots-hyprland) Hyprland dotfiles
(illogical-impulse, "ii", on Quickshell). It reads your Google Calendar and:

- shows the next meeting in the bar as `● 📅 HH:MM`, with a dot that is grey (> 15 min), green (> 5 min) or yellow (≤ 5 min);
- shows the meeting title on hover;
- 5 minutes before a meeting, shows a dismissable notification (no sound);
- when the meeting starts, raises a persistent card with *Join* (Meet link) and *Dismiss*, and rings
  repeatedly until you press one of them.

It only works with those dots: it patches ii's bar and relies on its components.

## Requirements

- [end-4/dots-hyprland](https://github.com/end-4/dots-hyprland) installed, with Quickshell and the ii config
  (`~/.config/quickshell/ii`)
- Python 3 (standard library only) and `pw-play` (PipeWire) for the sound
- A Google account that can see the calendar (see below)

## Google setup (once)

The widget is read-only (`calendar.readonly`) and talks to the Calendar API with your own OAuth client.

1. If the calendar belongs to a work account, share it with a personal Gmail with *See all event details*.
2. In [Google Cloud Console](https://console.cloud.google.com), with the personal account: create a project,
   enable **Google Calendar API**, configure the consent screen (*External*, *Testing*, add yourself as test user).
3. Create an **OAuth client ID** of type *Desktop app* and download the JSON.
4. Save it as `~/.config/calendarz/credentials.json` (`chmod 600`).
5. Sign in once:

   ```sh
   python3 plugin/gcal.py auth
   ```

Tokens are stored in `~/.config/calendarz/token.json`. While the consent screen is in *Testing*, the refresh token
expires every 7 days: the pill turns red ("Calendar: sign in again"); click it to re-authorize.

## Install

```sh
python3 install.py          # apply (idempotent)
python3 install.py status   # check what is in place
python3 install.py remove   # undo everything
```

`apply` symlinks `~/.config/quickshell/ii/calendarz` to `./plugin` and adds four lines (marked `// calendarz`) to
ii's `panelFamilies/IllogicalImpulseFamily.qml` and `modules/ii/bar/BarContent.qml`.

### After updating your dots

ii has no plugin system and its updater runs `rsync --delete` over `~/.config/quickshell/ii`, which wipes the
symlink and those lines. Re-run `python3 install.py`. If ii changed the anchor lines, the script stops with
`anchor not found`; update `PATCHES` in `install.py`.

## Usage

- Events are fetched every 2 minutes from all calendars selected in your Google account (all-day and declined
  events are skipped).
- Try the alert without a real meeting:

  ```sh
  qs -c ii ipc call meetings test
  ```

- Lead time and sound are `leadMinutes` and `soundFile` in `plugin/Meetings.qml`.
- After editing files in `plugin/`, reload ii with `touch ~/.config/quickshell/ii/shell.qml` (changes through the
  symlink do not trigger hot reload).
- The bar pill is only added to the horizontal bar; the alert card works with either.

## Credits

Designed and built together with [Claude Code](https://claude.com/claude-code) by Anthropic.
This project is not affiliated with or endorsed by Anthropic or by end-4.
