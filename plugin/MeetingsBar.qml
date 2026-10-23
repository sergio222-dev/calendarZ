import qs.modules.ii.bar
import QtQuick
import QtQuick.Layouts

// Bar entry for the next meeting; takes no space while there is nothing to show.
Loader {
    Layout.leftMargin: 4
    active: Meetings.shown

    sourceComponent: BarGroup {
        MeetingsPill {}
    }
}
