self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event) => {
    let data = { title: 'إشعار جديد', body: '' };
    if (event.data) {
        try { data = event.data.json(); }
        catch (e) { data.body = event.data.text(); }
    }
    const options = {
        body: data.body || '',
        vibrate: [200, 100, 200],
        tag: 'vodafone-notif',
        requireInteraction: true,
        data: { url: 'https://adamramy0109-pixel.github.io/vodafone/' }
    };
    event.waitUntil(
        self.registration.showNotification(data.title || 'إشعار', options)
    );
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const url = event.notification.data?.url || 'https://adamramy0109-pixel.github.io/vodafone/';
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then((windowClients) => {
            for (let client of windowClients) {
                if (client.url === url && 'focus' in client) return client.focus();
            }
            if (clients.openWindow) return clients.openWindow(url);
        })
    );
});
