def parse_hhmm(s: str) -> int:
    """Return total minutes since midnight for a HH:MM string."""
    h, m = map(int, s.split(":"))
    return h * 60 + m


def fmt_hhmm(minutes: int) -> str:
    """Format total minutes since midnight as HH:MM."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def plan_shuttle(
    matched_route: dict,
    from_stop: dict,
    to_stop: dict,
    query_minutes: int,
    service_end_minutes: int | None = None,
) -> list:
    """Return up to two upcoming shuttle trips between from_stop and to_stop.
    Returns empty list if no trips remain today.

    If service_end_minutes is set (last arrival of the service day from config hours),
    drop trips that depart or arrive after that time — e.g. a wrap-around leg on the
    last loop that would arrive after midnight is not a real trip."""
    anchor_arrivals = matched_route["stops"][0]["arrivals"]
    first_dep = parse_hhmm(anchor_arrivals[0])
    last_dep = parse_hhmm(anchor_arrivals[-1])
    interval = parse_hhmm(anchor_arrivals[1]) - first_dep

    from_offset = parse_hhmm(from_stop["arrivals"][0]) - first_dep
    to_offset = parse_hhmm(to_stop["arrivals"][0]) - first_dep
    wraps = to_offset < from_offset

    upcoming = []
    loop_start = first_dep
    while loop_start <= last_dep:
        departs = loop_start + from_offset
        arrives = loop_start + to_offset + (interval if wraps else 0)
        if departs >= query_minutes:
            upcoming.append({"departs": departs, "arrives": arrives})
        loop_start += interval

    if service_end_minutes is not None:
        upcoming = [
            t
            for t in upcoming
            if t["departs"] <= service_end_minutes and t["arrives"] <= service_end_minutes
        ]

    return upcoming