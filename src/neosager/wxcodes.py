"""Present-weather code sets. Single home for all MW/AW/AU code semantics.

Sources: ISD format document (docs/isd-format-document.pdf) —
MW = WMO 4677 manual present weather; AW = WMO 4680 automated present weather;
AU = METAR-style automated condition (subfield 3 = precipitation code).

MW precip: 50-75 drizzle/rain/snow, 77 snow grains, 79-90 ice pellets &
showers, 91-99 thunderstorm with precip. Excluded: 76 diamond dust and
78 ice crystals (non-measurable), and all codes <50 (fog, haze, "precip in
sight but not at station", "precip within past hour but not now" 20-29 —
counting those as current precip would poison labels).

AW precip: 40-49 is fog in 4680 (unlike 4677) so it is excluded; 50-92
covers drizzle/rain/snow/showers with precip at the station.
"""

MW_PRECIP = frozenset(range(50, 76)) | {77} | frozenset(range(79, 100))
MW_THUNDER = frozenset({17, 29}) | frozenset(range(91, 100))
# heavy-intensity manual codes used by the "stormy" conditions class
MW_HEAVY = frozenset({64, 65, 74, 75, 82, 84, 86, 88, 90, 92, 94, 97, 99})

AW_PRECIP = frozenset(range(50, 93))
AW_THUNDER = frozenset({90, 91, 92, 95})
AW_HEAVY = frozenset({54, 57, 59, 64, 67, 69, 74, 84, 86, 89, 90, 92})

# AU subfield-3 precipitation codes that indicate actual precipitation
# (1=drizzle, 2=rain, 3=snow, 4=snow grains, 5=ice crystals(excl), 6=ice
# pellets, 7=hail, 8=small hail, 9=missing -> we accept 1-4 and 6-8)
AU_PRECIP = frozenset({"1", "2", "3", "4", "6", "7", "8"})


def any_code_in(codes_str: str, code_set: frozenset[int]) -> bool:
    """'61,80' -> True if any code is in code_set. Tolerant of ''. """
    if not codes_str:
        return False
    return any(int(c) in code_set for c in codes_str.split(",") if c.isdigit())
