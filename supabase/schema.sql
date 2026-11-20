-- Portal Board on Supabase (applied to the "WSOC Project" Supabase project)
-- Every table has row level security on. Signed-in staff can read and write; anonymous visitors get nothing.

create table if not exists players (
  id            bigint generated always as identity primary key,
  player_key    text not null unique,          -- lower("team|last|first"), the stable link for notes and portal matches
  season        int  not null default 2026,
  conference    text not null,
  team          text not null,
  last_name     text not null,
  first_name    text not null,
  position      text,
  gp int, gs int, min numeric, g int, a int, pts int, pts_per_g numeric,
  sh int, sh_per_g numeric, sog int, yc int, rc int, gw int,
  pk int, pk_att int,                          -- blank for the 12 SEC teams on WMT Stats
  gk_gp int, gk_gs int, gk_min numeric, ga int, gaa numeric, sv int, sv_pct numeric,
  w int, l int, t int, sho int, sf int,        -- sf blank for WMT schools
  source        text,
  updated_at    timestamptz not null default now()
);

-- One row per dropped file
create table if not exists portal_uploads (
  id            bigint generated always as identity primary key,
  file_name     text,
  uploaded_by   uuid references auth.users(id) default auth.uid(),
  uploaded_at   timestamptz not null default now(),
  row_count     int not null default 0,
  new_row_count int not null default 0
);

-- One row per portal player ever seen. A later file only adds rows whose entry_key is new.
create table if not exists portal_entries (
  id              bigint generated always as identity primary key,
  entry_key       text not null unique,        -- normalized "name|school" from the file
  raw_name        text not null,
  raw_school      text,
  raw_row         jsonb,                       -- every column from the file, kept as sent
  first_upload_id bigint not null references portal_uploads(id),
  last_upload_id  bigint not null references portal_uploads(id),
  player_id       bigint references players(id),
  match_status    text not null check (match_status in ('matched','review','not_found','picked')),
  match_score     numeric,
  first_seen_at   timestamptz not null default now()
);

create table if not exists staff_notes (
  id          bigint generated always as identity primary key,
  player_id   bigint not null references players(id) on delete cascade,
  body        text not null check (length(body) between 1 and 4000),
  author_id   uuid not null references auth.users(id) default auth.uid(),
  author_email text default (auth.jwt() ->> 'email'),
  created_at  timestamptz not null default now()
);
create index if not exists staff_notes_player_idx on staff_notes(player_id, created_at desc);

alter table players        enable row level security;
alter table portal_uploads enable row level security;
alter table portal_entries enable row level security;
alter table staff_notes    enable row level security;

create policy "staff read players"   on players        for select to authenticated using (true);
create policy "staff read uploads"   on portal_uploads for select to authenticated using (true);
create policy "staff add uploads"    on portal_uploads for insert to authenticated with check (uploaded_by = (select auth.uid()));
create policy "staff read entries"   on portal_entries for select to authenticated using (true);
create policy "staff add entries"    on portal_entries for insert to authenticated with check (true);
create policy "staff fix matches"    on portal_entries for update to authenticated using (true) with check (true);
create policy "staff read notes"     on staff_notes    for select to authenticated using (true);
create policy "staff add notes"      on staff_notes    for insert to authenticated with check (author_id = auth.uid() and author_email is not distinct from (auth.jwt() ->> 'email'));
create policy "authors delete notes" on staff_notes    for delete to authenticated using (author_id = auth.uid());

-- live updates in the app when another staff member adds a note or a list
alter publication supabase_realtime add table staff_notes, portal_entries;

-- Temporary one-time loader (dropped after the 2026 stats are loaded): see migration one_time_player_loader.
