from __future__ import annotations

from guardian_shared.enums import EventState


ALLOWED_TRANSITIONS: dict[EventState, set[EventState]] = {
    EventState.NORMAL: {EventState.EVENT_DETECTED, EventState.RECORDED},
    EventState.EVENT_DETECTED: {EventState.RULE_CLASSIFIED, EventState.RECORDED},
    EventState.RULE_CLASSIFIED: {EventState.ACTION_PLANNED, EventState.RECORDED},
    EventState.ACTION_PLANNED: {
        EventState.AUTO_CONTROL,
        EventState.ASK_ELDER,
        EventState.FAMILY_ALERT,
        EventState.EMERGENCY_ALERT,
        EventState.RECORDED,
    },
    EventState.AUTO_CONTROL: {EventState.RECORDED, EventState.RESOLVED},
    EventState.ASK_ELDER: {EventState.WAIT_RESPONSE},
    EventState.WAIT_RESPONSE: {EventState.RESOLVED, EventState.FAMILY_ALERT, EventState.ESCALATED},
    EventState.FAMILY_ALERT: {EventState.RECORDED},
    EventState.EMERGENCY_ALERT: {EventState.RECORDED},
    EventState.RESOLVED: {EventState.RECORDED},
    EventState.ESCALATED: {EventState.FAMILY_ALERT, EventState.RECORDED},
    EventState.RECORDED: set(),
}


def can_transition(current: EventState | str, target: EventState | str) -> bool:
    current_state = EventState(current)
    target_state = EventState(target)
    return target_state in ALLOWED_TRANSITIONS.get(current_state, set())

