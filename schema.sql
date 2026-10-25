CREATE TABLE IF NOT EXISTS users (
  user_id SERIAL PRIMARY KEY,
  auth0_id VARCHAR(128) UNIQUE NOT NULL,
  username VARCHAR(80) NOT NULL,
  email VARCHAR(256) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS videos (
  video_id BIGSERIAL PRIMARY KEY,
  author_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  title VARCHAR(200) NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  video_url TEXT NOT NULL,
  category VARCHAR(50) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_missions (
  mission_date DATE NOT NULL,
  category VARCHAR(50) NOT NULL,
  mission TEXT NOT NULL,
  PRIMARY KEY (mission_date, category)
);

CREATE TABLE IF NOT EXISTS comments (
  comment_id SERIAL PRIMARY KEY,
  video_id BIGINT NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,
  author_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS video_likes (
  user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  video_id BIGINT NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (user_id, video_id)
);

CREATE TABLE IF NOT EXISTS subscription (
  my_id INT NOT NULL REFERENCES users(user_id),
  user_id INT NOT NULL REFERENCES users(user_id),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (my_id, user_id)
);

CREATE TABLE IF NOT EXISTS guests (
  guest_id TEXT PRIMARY KEY,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS preview_views (
  preview_id BIGSERIAL PRIMARY KEY,
  user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
  guest_id TEXT REFERENCES guests(guest_id) ON DELETE CASCADE,
  video_id BIGINT NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,
  view_date DATE NOT NULL,
  viewed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CHECK ((user_id IS NOT NULL AND guest_id IS NULL)
      OR (user_id IS NULL AND guest_id IS NOT NULL)),
  UNIQUE (user_id, view_date, video_id),
  UNIQUE (guest_id, view_date, video_id)
);

ALTER TABLE videos
  ADD COLUMN IF NOT EXISTS media_type TEXT NOT NULL DEFAULT 'video'
    CHECK (media_type IN ('image', 'video')),
  ADD COLUMN IF NOT EXISTS mission_date DATE;

ALTER TABLE videos DROP CONSTRAINT IF EXISTS fk_video_mission;
ALTER TABLE videos ADD CONSTRAINT fk_video_mission
  FOREIGN KEY (mission_date, category) REFERENCES daily_missions(mission_date, category);

ALTER TABLE comments ALTER COLUMN video_id TYPE BIGINT;
ALTER TABLE video_likes ALTER COLUMN video_id TYPE BIGINT;
ALTER TABLE subscription ALTER COLUMN my_id SET NOT NULL;
ALTER TABLE subscription ALTER COLUMN user_id SET NOT NULL;
