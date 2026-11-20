# Open questions

## Product name

Decided: **Thermogeist**, domain `thermogeist`. Tagline idea: "From poltergeist to thermogeist".
No GitHub repositories with this name were found on 2026-11-20.

Still to check before going public:
- trademark registers (DPMA, EUIPO) for "Thermogeist"
- HACS default repository list and HA brands repository
- availability of web domains and social handles

Should a rename ever be needed, it affects: folder under `custom_components/`, `DOMAIN` in
`const.py`, `manifest.json`, `hacs.json`, `pyproject.toml`, imports in tests,
`scripts/build_zip.sh`, release workflow, README files, docs.

## Design outdoor temperature by location (MDL-018)

Need a table that may be redistributed under MIT. The DIN/TS 12831-1 postcode table is DIN
content. Candidate: compute values from open DWD climate data with the method of the standard.

## Logo

Decided: thermostat with visor (see `spec/brand.md`). Open: outline the wordmark text (BRD-005).

## Device checklist (before finalising adapters)

Test setup: pipe probe (e.g. SNZB-02LD) on the flow pipe at the valve, values in InfluxDB.

| Question | Sonoff TRVZB | Bosch BTH-RA |
|---|---|---|
| Does the device hold a set valve position for hours? | open | open (overnight test at 39 % without result) |
| Where does flow start, how much does it scatter over days and after recalibration? | open | 10–20 % observed |
| Difference when approaching from above vs. below (backlash)? | open | open |
| How fast does the device report a turn of the knob? | open | open |
| When is an external temperature considered stale? | open | 30 min (per Z2M docs) |
| Battery drain with frequent position commands? | open | open |
| In which `operating_mode` does writing `pi_heating_demand` take effect? | – | open |

## Controller findings from the simulator (M3)

- The Bosch HT II scatter of the opening point (10–20 %) is not modelled yet; the simulator uses
  a fixed 10 %. Add scatter and backlash (TST-011) before tuning further.
- Oversized radiators (guest bathroom) cycle between about 12 % and 40 % a few times a day with
  the heat-pump profile. Check on the real device whether this is acceptable.

## Control mode (M4) – to verify on real devices

- Bosch BTH-RA: does `operating_mode: manual` keep a written `pi_heating_demand`? If not,
  write verification (ACT-043) switches the room back to observe and says so.
- Sonoff TRVZB / TRV-ZBT: control is implemented through the same roles but not yet tested on a
  real device.
- Override duration options (OVR-010) follow with schedules; until then a manual change is the
  new room setpoint.

## Open domain questions

- Thresholds for "significant jump" in the learning state (LRN-011).
- Default minimum opening in the heat-pump profile: 40 % as a start value. Field experience with the
  Bosch HT II: flow is not guaranteed at 20 %, likely at 25 %, safe at 30 %. Replaced per
  thermostat by CTL-023 once measured.
- Whether the heating curve is needed as an input at all when a flow sensor exists.
