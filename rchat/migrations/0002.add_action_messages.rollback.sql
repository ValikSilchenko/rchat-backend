alter table "chat" add column "created_by" uuid references "user" ("id");

with t as (
    select "user_initiated_action", "chat_id" from "message"
    where type = 'created_chat'
)
update "chat" set "created_by" = t."user_initiated_action"
from t where t."chat_id" = "chat"."id";

alter table "message" drop column user_initiated_action;
alter table "message" drop column user_involved;
