const chromeEndpoint = "http://127.0.0.1:9222";
const appUrl = process.env.APP_URL || "http://localhost:3000";

let id = 0;
const pending = new Map();

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

async function connect() {
  let target = await fetch(`${chromeEndpoint}/json/list`)
    .then((response) => response.json())
    .then((targets) => targets.find((item) => item.type === "page"));
  if (!target) {
    target = await fetch(`${chromeEndpoint}/json/new`, { method: "PUT" }).then((response) =>
      response.json(),
    );
  }
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener("open", resolve, { once: true });
    ws.addEventListener("error", reject, { once: true });
  });
  ws.addEventListener("message", (event) => {
    const payload = JSON.parse(event.data);
    if (payload.id && pending.has(payload.id)) {
      const { resolve, reject } = pending.get(payload.id);
      pending.delete(payload.id);
      if (payload.error) reject(new Error(payload.error.message));
      else resolve(payload.result);
    }
  });
  return ws;
}

function send(ws, method, params = {}) {
  const messageId = ++id;
  ws.send(JSON.stringify({ id: messageId, method, params }));
  return new Promise((resolve, reject) => {
    pending.set(messageId, { resolve, reject });
    setTimeout(() => {
      if (pending.has(messageId)) {
        pending.delete(messageId);
        reject(new Error(`CDP timeout: ${method}`));
      }
    }, 10000);
  });
}

async function evaluate(ws, expression) {
  const result = await send(ws, "Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
  if (result.exceptionDetails) {
    throw new Error(result.exceptionDetails.text || "Runtime evaluation failed");
  }
  return result.result.value;
}

async function waitFor(ws, expression, timeoutMs = 10000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const value = await evaluate(ws, expression);
    if (value) return value;
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Timed out waiting for: ${expression}`);
}

async function main() {
  const ws = await connect();
  await send(ws, "Page.enable");
  await send(ws, "Runtime.enable");

  await send(ws, "Page.navigate", { url: `${appUrl}/cars/xuv700` });
  await waitFor(ws, "document.readyState === 'complete'");
  const catalogText = await evaluate(ws, "document.body.innerText");
  assert(catalogText.includes("Mahindra XUV700"), "Catalog title missing");
  assert(catalogText.includes("Sophisticated Variants"), "Variant section missing");

  await evaluate(ws, "document.querySelector('button[aria-label=\"Toggle chat\"]').click()");
  await waitFor(ws, "document.body.innerText.includes('AutoElite Assistant')");

  await evaluate(
    ws,
    `(() => {
      const input = document.querySelector('input[placeholder="Ask anything..."]');
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
      setter.call(input, 'What is the on road price and ADAS level?');
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.closest('form').querySelector('button[aria-label="Send message"]').click();
      return true;
    })()`,
  );
  await waitFor(
    ws,
    "document.body.innerText.toLowerCase().includes('sales story') || document.body.innerText.toLowerCase().includes('couldn')",
    45000,
  );
  await waitFor(ws, "!document.querySelector('button[aria-label=\"Send message\"]').disabled", 15000);

  await evaluate(
    ws,
    `(() => {
      const input = document.querySelector('input[placeholder="Ask anything..."]');
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
      setter.call(input, 'Can a consultant call me for AX7 Luxury pricing?');
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.closest('form').querySelector('button[aria-label="Send message"]').click();
      return true;
    })()`,
  );
  await waitFor(ws, "document.body.innerText.toLowerCase().includes('confirm callback')", 15000);
  await evaluate(
    ws,
    `(() => {
      const name = [...document.querySelectorAll('input')].find((input) => input.placeholder === 'Name');
      const phone = [...document.querySelectorAll('input')].find((input) => input.placeholder === 'Phone');
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
      const setValue = (input, value) => {
        input.focus();
        setter.call(input, value);
        input.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: value }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
      };
      setValue(name, 'Black Box Buyer');
      setValue(phone, '+91 97777 12345');
      phone.closest('form').querySelector('button').click();
      return true;
    })()`,
  );
  await waitFor(ws, "document.body.innerText.includes('Lead captured') || document.body.innerText.includes('consultant panel')", 15000);

  await send(ws, "Page.navigate", { url: `${appUrl}/consultant` });
  await waitFor(ws, "document.readyState === 'complete'");
  await waitFor(ws, "document.body.innerText.includes('Black Box Buyer')", 15000);
  const consultantText = await evaluate(ws, "document.body.innerText");
  assert(consultantText.includes("+91 97777 12345"), "Captured phone missing in consultant panel");

  ws.close();
  console.log("blackbox-ui: passed");
}

main().catch((error) => {
  console.error(`blackbox-ui: failed - ${error.message}`);
  process.exit(1);
});
