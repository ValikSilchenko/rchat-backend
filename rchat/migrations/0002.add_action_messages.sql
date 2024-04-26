alter table "message" add column user_initiated_action uuid references "user" ("id");
alter table "message" add column user_involved uuid references "user" ("id");

with t as (
    select "created_by", "id" from "chat"
    where "created_by" is not null
)
update "message" set "user_initiated_action" = t."created_by"
from t where t."id" = "message"."chat_id" and type = 'created_chat';

alter table "chat" drop column "created_by";
