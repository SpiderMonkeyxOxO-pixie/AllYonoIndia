"""Staged posts published one per day by publish-scheduled-posts.py.

Each post's full page lives in tools/scheduled/<slug>/index.html (not web-served) with
{{DATE_ISO}} / {{DATE_HUMAN}} placeholders. On its published_date the publisher renders it
into blog/<slug>/, unlinks references to staged posts that are not live yet, and lists it.
Add a post: put its page in tools/scheduled/<slug>/ and append an entry below."""

SCHEDULED_POSTS = [
    {
        "slug": "yono-games-available-in-india-meaning",
        "published_date": "2026-09-29",
        "title": "What Does \"Available in India\" Actually Mean for a Yono Game App?",
        "eyebrow": "India Status",
        "excerpt": "\"Available in India\" is not the same as \"the link opens\". The four checks behind an India availability status, and what it does not tell you.",
        "image_alt": "Checklist graphic explaining what available in India means for a Yono game app",
        "cover_image": "/assets/images/blog/yono-games-available-in-india-meaning.webp"
    },
    {
        "slug": "india-availability-vs-legal-status",
        "published_date": "2026-09-30",
        "title": "India Availability vs Legal Status: Why They Are Not the Same",
        "eyebrow": "Legal Information",
        "excerpt": "A Yono game app can be reachable in India and still be prohibited. How availability differs from legal status under the Online Gaming Act, 2025.",
        "image_alt": "Two separate status boxes for India availability and legal status",
        "cover_image": "/assets/images/blog/india-availability-vs-legal-status.webp"
    },
    {
        "slug": "confirmed-vs-unverified-vs-not-yet-reviewed",
        "published_date": "2026-10-01",
        "title": "Confirmed vs Unverified vs Not Yet Reviewed: What Each Status Means",
        "eyebrow": "India Status",
        "excerpt": "How to read the India-Specific Status panel on a game page: what each label means, what moves it, and worked examples.",
        "image_alt": "Status label chart showing Confirmed, Unverified and Not Yet Reviewed",
        "cover_image": "/assets/images/blog/confirmed-vs-unverified-vs-not-yet-reviewed.webp"
    },
    {
        "slug": "download-link-not-proof-of-india-availability",
        "published_date": "2026-10-02",
        "title": "Why a Working Download Link Does Not Prove a Yono App Is Available in India",
        "eyebrow": "India Status",
        "excerpt": "A download link that opens proves only that a file is online today. Why links rotate, what they cannot tell you, and what to check instead.",
        "image_alt": "Graphic showing a download link next to a question mark about India availability",
        "cover_image": "/assets/images/blog/download-link-not-proof-of-india-availability.webp"
    },
    {
        "slug": "yono-games-kyc-requirement-proof",
        "published_date": "2026-10-03",
        "title": "What Counts as Proof That a Yono Game Requires KYC?",
        "eyebrow": "Account Safety",
        "excerpt": "The evidence that shows an app really requires KYC, the difference between 'KYC required' and 'KYC mentioned', and fake-KYC scams to avoid.",
        "image_alt": "Graphic about KYC evidence for Yono game apps with a document and shield icon",
        "cover_image": "/assets/images/blog/yono-games-kyc-requirement-proof.webp"
    },
    {
        "slug": "yono-games-upi-support-proof",
        "published_date": "2026-10-04",
        "title": "What Counts as Proof That a Yono Game Supports UPI?",
        "eyebrow": "Payments",
        "excerpt": "Most 'UPI supported' claims are marketing. The evidence ladder we use, why a screenshot is weak proof, and what the 2025 Act says about payments.",
        "image_alt": "Evidence ladder graphic for UPI support claims on Yono game apps",
        "cover_image": "/assets/images/blog/yono-games-upi-support-proof.webp"
    },
    {
        "slug": "yono-rummy-51-bonus-india-status",
        "published_date": "2026-10-06",
        "title": "Yono Rummy 51 Bonus: What Is Verified in India (2026)",
        "eyebrow": "Bonuses",
        "excerpt": "Is the Yono Rummy 51 bonus real? See what the ₹51 claim means, what is confirmed, what isn't, and how to check an app's offer yourself in India.",
        "image_alt": "Coupon-style card showing a 51 rupee bonus with an unverified stamp and a magnifying glass",
        "cover_image": "/assets/images/blog/yono-rummy-51-bonus-india-status.webp"
    },
    {
        "slug": "rummy-51-bonus-app-what-it-means",
        "published_date": "2026-10-07",
        "title": "Rummy 51 Bonus App: What the Claim Means in India (2026)",
        "eyebrow": "Bonuses",
        "excerpt": "Seeing \"rummy 51 bonus app\" lists everywhere? Learn what the ₹51 label means, why lists repeat it, and how to judge any bonus claim before you act.",
        "image_alt": "Three steps from advertisement to terms to in-app offer for a rummy 51 bonus claim",
        "cover_image": "/assets/images/blog/rummy-51-bonus-app-what-it-means.webp"
    },
    {
        "slug": "spin-crush-apk-download",
        "published_date": "2026-10-08",
        "title": "Spin Crush APK Download: What to Check First (2026)",
        "eyebrow": "APK Checks",
        "excerpt": "Looking for the Spin Crush APK? See what a download link does and does not prove, which details to verify, and how to stay safe before installing.",
        "image_alt": "APK file icon with a shield and a checklist of source, package name and permissions",
        "cover_image": "/assets/images/blog/spin-crush-apk-download.webp"
    },
    {
        "slug": "yono-games-apk-old-version-vs-new",
        "published_date": "2026-10-09",
        "title": "Yono Games APK Old Version vs New: Which to Trust (2026)",
        "eyebrow": "APK Checks",
        "excerpt": "Thinking of downloading an old version of the Yono Games APK? Learn the risks, how to compare versions, and why the newest file is not always the safest.",
        "image_alt": "Two phones comparing an old and a new app version on a balance scale",
        "cover_image": "/assets/images/blog/yono-games-apk-old-version-vs-new.webp"
    },
    {
        "slug": "yono-arcade-pure-apk-vs-arcade-mall",
        "published_date": "2026-10-10",
        "title": "Yono Arcade Pure APK vs Arcade Mall: What's the Difference?",
        "eyebrow": "APK Checks",
        "excerpt": "\"Pure APK\" and \"Arcade Mall\" appear in Yono Arcade searches. Learn what each label can mean, why it matters for safety, and how to verify before installing.",
        "image_alt": "A single app tile compared with a hub of many game tiles under a magnifying glass",
        "cover_image": "/assets/images/blog/yono-arcade-pure-apk-vs-arcade-mall.webp"
    },
    {
        "slug": "rummy-nabob-apk-download",
        "published_date": "2026-10-11",
        "title": "Rummy Nabob APK Download: Who Runs It? Verify First (2026)",
        "eyebrow": "Verification",
        "excerpt": "Searching \"rummy nabob apk\"? See what a rummy app name can and cannot tell you, how to identify the operator, and what to check before you install.",
        "image_alt": "Company building with a question mark, an ID card and a Not Yet Reviewed badge",
        "cover_image": "/assets/images/blog/rummy-nabob-apk-download.webp"
    },
    {
        "slug": "rummy-east-apk-download",
        "published_date": "2026-10-12",
        "title": "Rummy East APK Download: Does the Name Prove Anything?",
        "eyebrow": "Availability",
        "excerpt": "Rummy East APK searches are rising. See why a place word in an app name proves nothing about where it works, and how to check India availability properly.",
        "image_alt": "Compass and India map with a question mark showing that an app name proves nothing about availability",
        "cover_image": "/assets/images/blog/rummy-east-apk-download.webp"
    },
    {
        "slug": "rummy-perfect-apk-download",
        "published_date": "2026-10-13",
        "title": "Rummy Perfect APK: Why \"Perfect\" Claims Need Proof (2026)",
        "eyebrow": "Claims Check",
        "excerpt": "\"Perfect\" in an app name is a promise, not a fact. See how to audit big claims on a rummy app page and what to verify before installing Rummy Perfect.",
        "image_alt": "Clipboard of marketing claims with question marks under a Perfect banner",
        "cover_image": "/assets/images/blog/rummy-perfect-apk-download.webp"
    },
    {
        "slug": "rummy-wealth-apk-51-bonus",
        "published_date": "2026-10-14",
        "title": "Rummy Wealth 51 Bonus and APK: What Is Verified (2026)",
        "eyebrow": "Bonuses",
        "excerpt": "Rummy Wealth 51 bonus and APK searches explained. See what \"wealth\" money claims can and cannot mean, what is unverified, and how to check the offer.",
        "image_alt": "A 51 rupee coupon beside a terms and conditions document and a caution sign",
        "cover_image": "/assets/images/blog/rummy-wealth-apk-51-bonus.webp"
    },
    {
        "slug": "rummy-glee-apk-51-bonus",
        "published_date": "2026-10-15",
        "title": "Rummy Glee 51 Bonus: Types of Offers and What to Verify",
        "eyebrow": "Bonuses",
        "excerpt": "Rummy Glee 51 bonus explained: the difference between sign-up, deposit and referral offers, why offers expire, and how to verify what the app really gives.",
        "image_alt": "Stepped cards for sign-up, deposit, referral and event bonus types with a calendar",
        "cover_image": "/assets/images/blog/rummy-glee-apk-51-bonus.webp"
    },
    {
        "slug": "rummy-sun-51-bonus-explained",
        "published_date": "2026-10-16",
        "title": "Rummy Sun 51 Bonus: How Wagering Terms Work (Example)",
        "eyebrow": "Bonuses",
        "excerpt": "Rummy Sun 51 bonus explained with a simple worked example of wagering, expiry and withdrawal limits, so you can read any bonus terms before you act.",
        "image_alt": "Four connected steps showing a bonus, a play requirement, an expiry and a cap, marked as an example",
        "cover_image": "/assets/images/blog/rummy-sun-51-bonus-explained.webp"
    },
    {
        "slug": "rummy-gold-apk-download",
        "published_date": "2026-10-17",
        "title": "Rummy Gold APK vs Gold Rummy: Same App or Not? (2026)",
        "eyebrow": "Name Check",
        "excerpt": "Rummy Gold and Gold Rummy sound alike but may not be the same app. Learn how name mix-ups happen and how to confirm which app a download really is.",
        "image_alt": "Two similar app icons with reversed word order and different package names",
        "cover_image": "/assets/images/blog/rummy-gold-apk-download.webp"
    },
    {
        "slug": "new-yono-apps-india-review-status",
        "published_date": "2026-10-18",
        "title": "New Yono Apps in India (2026): Check Review Status First",
        "eyebrow": "New Apps",
        "excerpt": "New Yono apps launch constantly. Learn how to tell which ones have actually been reviewed for India, and the six checks to run before you install any.",
        "image_alt": "New app tiles above a review checklist with Confirmed, Unverified and Not Yet Reviewed labels",
        "cover_image": "/assets/images/blog/new-yono-apps-india-review-status.webp"
    },
    {
        "slug": "rummy-ola-apk-download",
        "published_date": "2026-10-19",
        "title": "Rummy Ola and Rummy Culture APK: Lookalike Name Risks",
        "eyebrow": "Lookalikes",
        "excerpt": "Rummy Ola APK and Rummy Culture APK searches explained. See how lookalike names are used, what to verify, and how to avoid installing the wrong file.",
        "image_alt": "Two app tiles with faint duplicate shadows and a magnifying glass comparing package names",
        "cover_image": "/assets/images/blog/rummy-ola-apk-download.webp"
    },
    {
        "slug": "yono-all-games-new-apk-explained",
        "published_date": "2026-10-20",
        "title": "Yono All Games New APK: What the Label Means (2026)",
        "eyebrow": "Labels",
        "excerpt": "\"Yono All Games new APK\" is a common search label, not an official product. See what it can refer to, why \"new\" proves little, and how to check a file.",
        "image_alt": "A hub icon connected to many app tiles with a dotted NEW label under a magnifying glass",
        "cover_image": "/assets/images/blog/yono-all-games-new-apk-explained.webp"
    }
]
