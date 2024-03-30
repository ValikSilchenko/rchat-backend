create table "photo" (
    id uuid primary key,
    size_bytes bigint not null,
    extension varchar(16) not null,
    created_timestamp timestamp not null default now()
);

create table "user" (
    id uuid primary key,
    public_id varchar(32) not null unique,
    password varchar(64) not null,
    email varchar(64) not null,
    user_salt varchar(32) not null,
    first_name varchar(32),
    last_name varchar(32),
    avatar_photo_id uuid references "photo" ("id"),
    profile_status varchar(64),
    profile_bio varchar(512),
    created_timestamp timestamp not null default (now() at time zone 'utc')
);
create table "session" (
    id uuid primary key,
    user_id uuid not null references "user" ("id"),
    ip varchar(15),
    user_agent varchar(64),
    is_active bool not null default true,
    created_timestamp timestamp not null default (now() at time zone 'utc')
);

create table "geoip" (
    ip varchar(15) primary key,
    state varchar(64),
    country varchar(64),
    city varchar(64),
    updated_timestamp timestamp not null,
    created_timestamp timestamp not null default now()
);

create table "chat" (
    id uuid primary key,
    type varchar(16) not null,
    avatar_photo_id uuid references "photo" ("id"),
    name varchar(32) not null,
    description varchar(256),
    created_timestamp timestamp not null default now()
);

create table "message" (
    id uuid primary key,
    chat_id uuid not null references "chat" ("id"),
    sender_user_id uuid not null references "user" ("id"),
    message_text varchar(4096),
    audio_msg_file_id uuid,
    video_msg_file_id uuid,
    reply_to_message uuid references "message" ("id"),
    forwarded_message uuid references "message" ("id"),
    is_silent bool not null default false,
    edited_at timestamp,
    created_timestamp timestamp not null default now()
);

