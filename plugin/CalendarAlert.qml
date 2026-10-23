import qs
import qs.modules.common
import qs.modules.common.widgets
import qs.services
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland

Scope {
    PanelWindow {
        id: root
        visible: Meetings.pending.length > 0 && !GlobalStates.screenLocked
        screen: Quickshell.screens.find(s => s.name === Hyprland.focusedMonitor?.name) ?? null

        WlrLayershell.namespace: "quickshell:calendarAlert"
        WlrLayershell.layer: WlrLayer.Overlay
        exclusiveZone: 0

        anchors.top: true
        margins.top: 12
        mask: Region { item: alerts }
        color: "transparent"
        implicitWidth: 400 + Appearance.sizes.elevationMargin * 2
        implicitHeight: alerts.implicitHeight + Appearance.sizes.elevationMargin * 2

        ColumnLayout {
            id: alerts
            anchors.centerIn: parent
            width: 400
            spacing: 8

            Repeater {
                model: Meetings.pending

                Rectangle {
                    id: card
                    required property var modelData
                    property int minutes: Meetings.minutesTo(modelData)

                    Layout.fillWidth: true
                    implicitHeight: content.implicitHeight + 24
                    radius: Appearance.rounding.normal
                    color: Appearance.m3colors.m3surfaceContainerHigh
                    border.width: 2
                    border.color: Appearance.m3colors.m3error

                    ColumnLayout {
                        id: content
                        anchors { fill: parent; margins: 12 }
                        spacing: 6

                        StyledText {
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                            text: card.modelData.title
                            font { pixelSize: Appearance.font.pixelSize.large; weight: Font.DemiBold }
                            color: Appearance.m3colors.m3onSurface
                        }
                        StyledText {
                            text: Qt.formatTime(new Date(card.modelData.start), "HH:mm") + "  ·  "
                                + (card.minutes > 0 ? Translation.tr("in %1 min").arg(card.minutes)
                                    : card.minutes === 0 ? Translation.tr("starting now")
                                    : Translation.tr("%1 min ago").arg(-card.minutes))
                            color: Appearance.m3colors.m3error
                            font.pixelSize: Appearance.font.pixelSize.small
                        }
                        RowLayout {
                            spacing: 6
                            RippleButton {
                                visible: card.modelData.link !== ""
                                buttonText: Translation.tr("Join")
                                colBackground: Appearance.colors.colPrimary
                                implicitHeight: 32
                                implicitWidth: 80
                                onClicked: {
                                    Qt.openUrlExternally(card.modelData.link);
                                    Meetings.dismiss(card.modelData);
                                }
                                contentItem: StyledText {
                                    horizontalAlignment: Text.AlignHCenter
                                    text: parent.buttonText
                                    color: Appearance.colors.colOnPrimary
                                }
                            }
                            RippleButton {
                                buttonText: Translation.tr("Dismiss")
                                implicitHeight: 32
                                implicitWidth: 80
                                onClicked: Meetings.dismiss(card.modelData)
                                contentItem: StyledText {
                                    horizontalAlignment: Text.AlignHCenter
                                    text: parent.buttonText
                                    color: Appearance.m3colors.m3onSurface
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
