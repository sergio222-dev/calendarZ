import qs.modules.common
import qs.modules.common.widgets
import qs.services
import qs.modules.ii.bar
import QtQuick
import QtQuick.Layouts

MouseArea {
    id: root
    implicitWidth: rowLayout.implicitWidth + 10 * 2
    implicitHeight: Appearance.sizes.barHeight

    hoverEnabled: true
    cursorShape: Meetings.status === "reauth" ? Qt.PointingHandCursor : Qt.ArrowCursor
    onClicked: if (Meetings.status === "reauth") Meetings.signIn()

    StyledPopup {
        hoverTarget: root
        active: root.containsMouse && Meetings.status === "ok" && Meetings.next !== null

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 4

            StyledPopupHeaderRow {
                icon: "event"
                label: Meetings.next?.title ?? ""
            }
            StyledPopupValueRow {
                icon: "schedule"
                label: Qt.formatTime(new Date(Meetings.next?.start), "HH:mm")
                value: Translation.tr("in %1 min").arg(Meetings.minutesTo(Meetings.next))
            }
        }
    }

    RowLayout {
        id: rowLayout
        anchors.centerIn: parent

        // Urgency dot: grey > 15 min, green > 5 min, yellow otherwise
        Rectangle {
            visible: Meetings.status === "ok" && Meetings.next !== null
            implicitWidth: 8
            implicitHeight: 8
            radius: 4
            Layout.alignment: Qt.AlignVCenter
            color: {
                const min = (new Date(Meetings.next?.start).getTime() - Meetings.now) / 60000;
                return min > 15 ? "#9e9e9e" : min > 5 ? "#4caf50" : "#fbc02d";
            }
        }

        MaterialSymbol {
            fill: 0
            text: Meetings.status === "ok" ? "event" : "event_busy"
            iconSize: Appearance.font.pixelSize.large
            color: Meetings.status === "ok" ? Appearance.colors.colOnLayer1 : Appearance.m3colors.m3error
            Layout.alignment: Qt.AlignVCenter
        }

        StyledText {
            Layout.alignment: Qt.AlignVCenter
            Layout.maximumWidth: 220
            elide: Text.ElideRight
            font.pixelSize: Appearance.font.pixelSize.small
            color: Meetings.status === "ok" ? Appearance.colors.colOnLayer1 : Appearance.m3colors.m3error
            text: Meetings.status === "reauth" ? Translation.tr("Calendar: sign in again")
                : Meetings.status === "error" ? Translation.tr("Calendar unreachable")
                : Meetings.next ? Qt.formatTime(new Date(Meetings.next.start), "HH:mm") : ""
        }
    }
}
