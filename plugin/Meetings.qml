pragma Singleton
pragma ComponentBehavior: Bound

import Quickshell
import Quickshell.Io
import QtQuick

/**
 * Upcoming Google Calendar meetings plus the alerts raised for them.
 * Data comes from scripts/calendar/gcal.py (run `gcal.py auth` once to sign in).
 */
Singleton {
    id: root

    readonly property int leadMinutes: 5
    readonly property int pollInterval: 120000
    readonly property string soundFile: "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"
    readonly property string scriptPath: Quickshell.shellPath("calendarz/gcal.py")

    property var events: []
    property string status: "ok" // ok | reauth | error
    property var pending: []     // meetings currently alerting, until dismissed
    property real now: Date.now()
    property var alerted: ({})

    readonly property var next: events.find(e => minutesTo(e) >= 0) ?? null
    readonly property bool shown: status !== "ok" || next !== null

    function minutesTo(e) {
        return Math.round((new Date(e.start).getTime() - now) / 60000);
    }

    function check() {
        now = Date.now();
        for (const e of events) {
            const key = e.id + "|" + e.start;
            const delta = new Date(e.start).getTime() - now;
            if (alerted[key] || delta > leadMinutes * 60000 || delta < -5 * 60000)
                continue;
            alerted[key] = true;
            alert(e);
        }
    }

    function alert(e) {
        pending = pending.concat([e]);
        Quickshell.execDetached(["pw-play", soundFile]);
    }

    // Try the alert without a real meeting: qs -c ii ipc call meetings test
    IpcHandler {
        target: "meetings"

        function test(): void {
            const start = new Date(Date.now() + 2 * 60000).toISOString();
            root.alert({id: "test-" + Date.now(), title: "Test meeting", start: start, link: "https://meet.google.com"});
        }
    }

    function dismiss(e) {
        // Compare by key: a delegate's modelData is not guaranteed to be the same JS object.
        pending = pending.filter(p => p.id !== e.id || p.start !== e.start);
    }

    function signIn() {
        login.running = true;
    }

    Process {
        id: fetch
        command: ["python3", root.scriptPath, "events"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const d = JSON.parse(text);
                    if (d.error) {
                        root.status = d.error;
                    } else {
                        root.status = "ok";
                        root.events = d.events;
                    }
                } catch (err) {
                    root.status = "error";
                }
                root.check();
            }
        }
    }

    Process {
        id: login
        command: ["python3", root.scriptPath, "auth"]
        onRunningChanged: if (!running) fetch.running = true
    }

    Timer {
        interval: root.pollInterval
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: if (!fetch.running) fetch.running = true
    }

    // Keep ringing until every pending meeting is dismissed or joined.
    Timer {
        interval: 5000
        running: root.pending.length > 0
        repeat: true
        onTriggered: Quickshell.execDetached(["pw-play", root.soundFile])
    }

    Timer {
        interval: 15000
        running: true
        repeat: true
        onTriggered: root.check()
    }
}
