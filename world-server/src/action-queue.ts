import type { ActionRequest, ActionResult } from './types.js';
import { processAction } from './event-processor.js';

type QueueEntry = {
  req: ActionRequest;
  resolve: (result: ActionResult) => void;
};

const queue: QueueEntry[] = [];
let processing = false;

async function drain(): Promise<void> {
  if (processing) return;
  processing = true;

  while (queue.length > 0) {
    const entry = queue.shift()!;
    try {
      const result = await processAction(entry.req);
      entry.resolve(result);
    } catch (err) {
      console.error('[ActionQueue] Error processing action:', err);
      entry.resolve({ accepted: false, reason: 'Internal server error' });
    }
  }

  processing = false;
}

export function enqueueAction(req: ActionRequest): Promise<ActionResult> {
  return new Promise(resolve => {
    queue.push({ req, resolve });
    void drain();
  });
}
