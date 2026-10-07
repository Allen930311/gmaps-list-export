# AGENT_CONTEXT — gmaps-list-export

> Fresh-agent entrypoint. Classification: **UTILITY**.

## Purpose

A small command-line tool that exports a publicly shared Google Maps saved list
to CSV, Markdown or JSON.

## Operating boundary

`README.md` owns usage, output shape and known limitations.
`gmaps_list_export.py` is the implementation.

This repository has no standing product roadmap. A fresh agent should maintain
or fix the exporter only when a concrete task exists; do not expand it into a
general Maps automation platform by default.

Google Maps DOM behavior is external and changeable. Reproduce a current failure
before changing selectors.

## Data / safety

Only publicly shared lists are in scope. Do not add login/session scraping,
cookies or private-list access unless Allen separately authorizes that new
boundary.

## Remote vs local truth

Remote `main` is shared source truth. Browser sessions, generated exports and
local Playwright state are runtime/local artifacts.
