import re
import glob

html_files = ["MobileHome.html", "MobileScans.html", "MobileInsights.html", "MobileProfile.html"]

notification_logic = """
<script>
    async function loadNotifications() {
        const userEmail = localStorage.getItem("userEmail");
        if (!userEmail) return;
        
        try {
            const res = await fetch(`https://payder.onrender.com/user/notifications?user_email=${encodeURIComponent(userEmail)}`);
            const data = await res.json();
            
            const dot = document.getElementById("nav-bell-dot");
            if (data.count > 0) {
                dot.classList.remove("hidden");
                // Attach data to bell
                document.getElementById("nav-bell").onclick = async () => {
                    const msgs = data.notifications.map(n => n.message).join("\\n\\n");
                    alert(`New Notifications:\\n\\n${msgs}`);
                    
                    await fetch("https://payder.onrender.com/user/notifications/read", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ user_email: userEmail })
                    });
                    dot.classList.add("hidden");
                };
            } else {
                dot.classList.add("hidden");
                document.getElementById("nav-bell").onclick = () => {
                    alert("No new notifications.");
                };
            }
        } catch(e) { console.error(e); }
    }
    loadNotifications();
</script>
</body>
"""

for fname in html_files:
    with open(fname, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 1. Update the bell button
    old_bell = '''<button class="bg-white text-gray-600 hover:bg-gray-50 transition-colors active:scale-95 w-10 h-10 rounded-full flex items-center justify-center shadow-sm relative">
                                                                                        <span class="material-symbols-outlined text-[20px]" style="font-variation-settings: 'FILL' 0;">notifications</span>
                                                                                        <span class="absolute top-2 right-2 w-2 h-2 bg-error rounded-full border border-white"></span>
                                                                                </button>'''
    
    new_bell = '''<button id="nav-bell" class="bg-white text-gray-600 hover:bg-gray-50 transition-colors active:scale-95 w-10 h-10 rounded-full flex items-center justify-center shadow-sm relative">
                                                                                        <span class="material-symbols-outlined text-[20px]" style="font-variation-settings: 'FILL' 0;">notifications</span>
                                                                                        <span id="nav-bell-dot" class="absolute top-2 right-2 w-2 h-2 bg-error rounded-full border border-white hidden"></span>
                                                                                </button>'''
    
    # Using regex to make it robust against indentation differences
    pattern = re.compile(r'<button class="bg-white text-gray-600 hover:bg-gray-50 transition-colors active:scale-95 w-10 h-10 rounded-full flex items-center justify-center shadow-sm relative">\s*<span class="material-symbols-outlined text-\[20px\]" style="font-variation-settings: \'FILL\' 0;">notifications</span>\s*<span class="absolute top-2 right-2 w-2 h-2 bg-error rounded-full border border-white"></span>\s*</button>')
    
    html = pattern.sub(new_bell.strip(), html)
    
    # 2. Append notification logic before </body>
    html = html.replace('</body>', notification_logic)
    
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(html)
