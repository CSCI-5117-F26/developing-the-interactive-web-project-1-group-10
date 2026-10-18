CREATE TABLE users (
  user_id SERIAL PRIMARY KEY,
  auth0_id VARCHAR(128) UNIQUE NOT NULL,
  username VARCHAR(80) NOT NULL,
  email VARCHAR(256) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE videos (
  video_id BIGSERIAL PRIMARY KEY,
  author_id INT NOT NULL,
  title VARCHAR(200) NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  video_url TEXT NOT NULL,
  category VARCHAR(50) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT fk_video_author
    FOREIGN KEY (author_id) REFERENCES users(user_id)
    ON DELETE CASCADE
);

CREATE TABLE comments (
  comment_id SERIAL PRIMARY KEY,
  video_id INT NOT NULL,
  author_id INT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  
  CONSTRAINT fk_comment_post
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
    ON DELETE CASCADE,

  CONSTRAINT fk_comment_author
    FOREIGN KEY (author_id) REFERENCES users(user_id)
    ON DELETE CASCADE
);

CREATE TABLE video_likes (
  user_id INT,
  video_id INT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (user_id, video_id),
  CONSTRAINT fk_post_like_user
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    ON DELETE CASCADE,

  CONSTRAINT fk_post_like_post
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
    ON DELETE CASCADE
);
