alter table "message" add column user_initiated_action uuid references "user" ("id");
alter table "message" add column user_involved uuid references "user" ("id");
