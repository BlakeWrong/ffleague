interface QueueItem {
  id: string;
  priority: number;
  apiCall: () => Promise<unknown>;
  resolve: (value: unknown) => void;
  reject: (reason?: Error) => void;
  component?: string;
  url?: string;
  addedAt: number;
}

type QueueOrder = 'fifo' | 'lifo' | 'priority' | 'component-grouped';

class APIQueue {
  private queue: QueueItem[] = [];
  private isProcessing = false;
  private order: QueueOrder = 'priority';
  private delay = 100; // ms between requests
  private activeRequests = new Set<string>();

  setOrder(order: QueueOrder) {
    this.order = order;
  }

  setDelay(ms: number) {
    this.delay = ms;
  }

  async add<T>(
    apiCall: () => Promise<T>,
    options: {
      priority?: number;
      component?: string;
      url?: string;
      id?: string;
    } = {}
  ): Promise<T> {
    const {
      priority = 5, // 1 = highest, 10 = lowest
      component = 'unknown',
      url = 'unknown',
      id = `${component}-${Date.now()}-${Math.random()}`
    } = options;

    return new Promise<T>((resolve, reject) => {
      const queueItem: QueueItem = {
        id,
        priority,
        apiCall: apiCall as () => Promise<unknown>,
        resolve: resolve as (value: unknown) => void,
        reject,
        component,
        url,
        addedAt: Date.now()
      };

      this.queue.push(queueItem);
      this.sortQueue();
      this.processQueue();
    });
  }

  private sortQueue() {
    switch (this.order) {
      case 'priority':
        this.queue.sort((a, b) => a.priority - b.priority);
        break;
      case 'lifo':
        // Reverse order (last-in-first-out)
        this.queue.sort((a, b) => b.addedAt - a.addedAt);
        break;
      case 'component-grouped':
        // Group by component, then by priority
        this.queue.sort((a, b) => {
          if (a.component !== b.component) {
            return a.component!.localeCompare(b.component!);
          }
          return a.priority - b.priority;
        });
        break;
      case 'fifo':
      default:
        // Keep original order (first-in-first-out)
        this.queue.sort((a, b) => a.addedAt - b.addedAt);
        break;
    }
  }

  private async processQueue() {
    if (this.isProcessing || this.queue.length === 0) {
      return;
    }

    this.isProcessing = true;

    while (this.queue.length > 0) {
      const queueItem = this.queue.shift();
      if (queueItem) {
        try {
          console.log(`🔄 Processing API call: ${queueItem.component} - ${queueItem.url} (Priority: ${queueItem.priority})`);
          this.activeRequests.add(queueItem.id);

          const result = await queueItem.apiCall();
          queueItem.resolve(result);

          this.activeRequests.delete(queueItem.id);
          console.log(`✅ Completed API call: ${queueItem.component} - ${queueItem.url}`);

          // Delay between requests
          if (this.queue.length > 0) {
            await new Promise(resolve => setTimeout(resolve, this.delay));
          }
        } catch (error) {
          console.error(`❌ API queue error for ${queueItem.component}:`, error);
          queueItem.reject(error instanceof Error ? error : new Error(String(error)));
          this.activeRequests.delete(queueItem.id);
        }
      }
    }

    this.isProcessing = false;
  }

  // Utility methods
  getQueueLength(): number {
    return this.queue.length;
  }

  isQueueProcessing(): boolean {
    return this.isProcessing;
  }

  getQueueStatus() {
    return {
      queueLength: this.queue.length,
      isProcessing: this.isProcessing,
      activeRequests: Array.from(this.activeRequests),
      order: this.order,
      delay: this.delay,
      nextItems: this.queue.slice(0, 3).map(item => ({
        component: item.component,
        priority: item.priority,
        url: item.url
      }))
    };
  }

  clearQueue() {
    this.queue.forEach(item => item.reject(new Error('Queue cleared')));
    this.queue = [];
  }

  // Priority shortcuts
  static PRIORITY = {
    CRITICAL: 1,    // League stats, standings
    HIGH: 2,        // User-facing data
    NORMAL: 5,      // Default
    LOW: 8,         // Background data
    LOWEST: 10      // Non-essential data
  } as const;
}

// Global API queue instance
export const apiQueue = new APIQueue();

// Helper function to wrap fetch calls
export async function queuedFetch(
  url: string,
  fetchOptions?: RequestInit,
  queueOptions?: {
    priority?: number;
    component?: string;
  }
): Promise<Response> {
  const { priority, component } = queueOptions || {};

  return apiQueue.add(
    () => fetch(url, fetchOptions),
    {
      priority,
      component,
      url,
    }
  );
}

// Export APIQueue class and priority constants for advanced usage
export { APIQueue };
export const PRIORITY = APIQueue.PRIORITY;