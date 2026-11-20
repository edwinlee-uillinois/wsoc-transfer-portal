# WSOC Transfer Portal Board

Staff web app for evaluating Power 4 women's soccer players and transfer portal lists.

**Live app:** https://edwinlee-uillinois.github.io/wsoc-transfer-portal/

## What's here

| Path | What it is |
| --- | --- |
| `index.html` | The Portal Board app (served by GitHub Pages). Staff sign in with their email and password; player stats, portal lists, and notes are stored in Supabase. |
| `offline/index.html` | Standalone copy with the stats embedded. Needs no sign-in; notes stay in the browser only. |
| `data/` | 2026 player stats CSVs (Big Ten and Power 4). |
| `supabase/schema.sql` | Database tables and row-level security policies. |
| `supabase/build_sb.py` | Script that builds the Supabase edition of the page. |

## Notes

- The page contains the Supabase project URL and the public (anon) key only. That key is safe to publish because every table is protected by row-level security that requires a signed-in staff account. Never commit the service-role key.
- Staff accounts are created in Supabase Auth. Keep public sign-ups turned off.
