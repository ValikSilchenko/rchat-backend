alter table "message" rename column reply_to_message_id to reply_to_message;
alter table "message" rename column forwarded_message_id to forwarded_message;
alter table "message" rename column user_initiated_action_id to user_initiated_action;
alter table "message" rename column user_involved_id to user_involved;