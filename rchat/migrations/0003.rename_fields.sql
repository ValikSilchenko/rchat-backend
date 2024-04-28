alter table "message" rename column "reply_to_message" to "reply_to_message_id";
alter table "message" rename column "forwarded_message" to "forwarded_message_id";
alter table "message" rename column "user_initiated_action" to "user_initiated_action_id";
alter table "message" rename column "user_involved" to "user_involved_id";