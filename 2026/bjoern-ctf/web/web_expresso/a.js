import express from "express";
import session from "express-session";
import bodyParser from "body-parser/json";
const PORT = 3000;

const users = {
  admin: {
    name: "Administrator",
    password: crypto.randomUUID(),
    isAdmin: 1,
  },
  pleb: {
    name: "Plebeian",
    password: crypto.randomUUID(),
    isAdmin: 0,
  }
};

const app = express();
app.use(bodyParser());

app.use(
  session({
    secret: crypto.randomUUID(),
    resave: false,
    saveUninitialized: false,
  }),
);

const requireAuth = (req, res, next) => {
  if (typeof req.session.username !== "string")
    return res.status(401).json({ bad: true });
  next();
};

app.post("/login", (req, res) => {
  const { username, password } = req.body;
  if (!username || typeof username !== "string") return res.status(400).send();
  const user = users[username];

  if (!user || !user.name || user.password !== password)
    return res.status(400).send();

  req.session.username = username;
  return res.status(200).json({ ok: true });
});

app.post("/update", requireAuth, (req, res) => {
  const body = req.body;
  if (body.isAdmin !== undefined) res.status(400).json({ lmao: "no?" });
  Object.assign(users[req.session.username], body);
  res.status(204).json({ ok: true });
});

app.get("/", requireAuth, (req, res) => {
  res.send("Hello World!");
});

app.get("/flag", requireAuth, (req, res) => {
  const user = users[req.session.username];
  if (!user || !user.isAdmin) return res.status(400).json({ ok: false });
  return res.json({ flag: process.env.FLAG ?? "flagbot{local_flag}" });
});

app.listen(PORT, () => {
  console.log(`Example app listening on port ${PORT}`);
});