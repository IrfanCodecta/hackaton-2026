// The event owns one shared destination; explicit alternate choices stay intact.
export function eventHost(saved, context) {
  return saved?.host || context.event_host;
}

// Read the already-visible range again, including edits and deletions, without
// collapsing older pages or remounting composers with unsent drafts.
export async function readThread(command, action, body, through, signal) {
  let result = await command(action, body, undefined, signal);
  const posts = [...result.posts];
  while (through && result.more && result.posts.length && result.posts.at(-1).id > through) {
    result = await command(action, {...body, before: result.posts.at(-1).id}, undefined, signal);
    posts.push(...result.posts);
  }
  return {...result, posts};
}

// Poll only a visible, online view. Focus/reconnection refresh immediately;
// slow reads never overlap, and leaving the view aborts its outstanding read.
export function watchVisible(refresh, onError, delay = 15000) {
  let stopped = false, timer, running = false, controller;
  const available = () => !document.hidden && navigator.onLine !== false;
  async function run() {
    clearTimeout(timer);
    if (stopped || running || !available()) return;
    running = true;
    controller = new AbortController();
    try { await refresh(controller.signal); }
    catch (error) { if (!stopped && error.name !== 'AbortError') onError(error); }
    finally {
      running = false;
      if (!stopped && available()) timer = setTimeout(run, delay);
    }
  }
  function wake() { if (available()) run(); else clearTimeout(timer); }
  document.addEventListener('visibilitychange', wake);
  window.addEventListener('focus', wake);
  window.addEventListener('online', wake);
  window.addEventListener('offline', wake);
  run();
  return () => {
    stopped = true;
    clearTimeout(timer);
    controller?.abort();
    document.removeEventListener('visibilitychange', wake);
    window.removeEventListener('focus', wake);
    window.removeEventListener('online', wake);
    window.removeEventListener('offline', wake);
  };
}
