"""Hindi / English text for the bot (Swati).

Every alert wording rule lives here: advisories never say "safe", RED says "prepare to
relocate" as an ADVISORY and points to the authorities, and UNKNOWN says explicitly that
it is not an all-clear. Have a native Hindi speaker (and a KVK/administration contact)
review these strings before the user trial.
"""
LEVEL_EMOJI = {"GREEN": "🟢", "UNKNOWN": "⚪", "YELLOW": "🟡", "ORANGE": "🟠", "RED": "🔴"}

LEVEL_NAME = {
    "en": {"GREEN": "No warning right now", "UNKNOWN": "Status unknown", "YELLOW": "Be aware",
           "ORANGE": "Be prepared", "RED": "Take action"},
    "hi": {"GREEN": "अभी कोई चेतावनी नहीं", "UNKNOWN": "स्थिति अज्ञात", "YELLOW": "सावधान रहें",
           "ORANGE": "तैयार रहें", "RED": "तुरंत कदम उठाएँ"},
}

FLOOD_ADVICE = {
    "en": {
        "GREEN": "No warning from our station right now. Conditions can change quickly - keep following official updates.",
        "UNKNOWN": "Our station is not reporting or a sensor has failed, so we cannot confirm conditions. This does NOT mean it is safe. Check IMD, CWC or local authority updates.",
        "YELLOW": "Heavy rain or rising water is possible. Stay alert, avoid crossing streams and low-lying roads, and follow local news.",
        "ORANGE": "Flooding is possible. Keep documents, medicines and a charged phone ready, move livestock and valuables to higher ground, and be ready to leave if the authorities ask.",
        "RED": "High flood risk. Prepare to move to a safe, higher place now, especially if you live near the river or in a low-lying area. This is an advisory, not an evacuation order - follow instructions from your district administration / State Disaster Management Authority. Emergency: 112, NDMA helpline 1078.",
    },
    "hi": {
        "GREEN": "हमारे स्टेशन से अभी कोई चेतावनी नहीं है। हालात जल्दी बदल सकते हैं - सरकारी सूचनाओं पर नज़र रखें।",
        "UNKNOWN": "हमारे स्टेशन से डेटा नहीं आ रहा या कोई सेंसर ख़राब है, इसलिए हम स्थिति की पुष्टि नहीं कर सकते। इसका मतलब यह नहीं कि सब सुरक्षित है। IMD, CWC या स्थानीय प्रशासन की जानकारी देखें।",
        "YELLOW": "भारी बारिश या जलस्तर बढ़ने की संभावना है। सतर्क रहें, नालों और निचले रास्तों को पार करने से बचें और स्थानीय समाचार देखते रहें।",
        "ORANGE": "बाढ़ की संभावना है। ज़रूरी कागज़ात, दवाइयाँ और चार्ज किया हुआ फ़ोन तैयार रखें, पशुओं और कीमती सामान को ऊँची जगह ले जाएँ, और प्रशासन के कहने पर निकलने के लिए तैयार रहें।",
        "RED": "बाढ़ का ख़तरा अधिक है। अभी सुरक्षित ऊँची जगह जाने की तैयारी करें, ख़ासकर अगर आप नदी के पास या निचले इलाक़े में रहते हैं। यह एक परामर्श है, निकासी का आदेश नहीं - अपने ज़िला प्रशासन / राज्य आपदा प्रबंधन प्राधिकरण के निर्देशों का पालन करें। आपातकाल: 112, NDMA हेल्पलाइन 1078।",
    },
}

HEAT_ADVICE = {
    "en": {
        "GREEN": "No heat warning right now.",
        "UNKNOWN": "Our station is not reporting, so we cannot confirm the temperature. Check IMD updates.",
        "YELLOW": "It is very hot and humid. Drink water often, avoid heavy work in the afternoon and wear light clothes.",
        "ORANGE": "Severe heat. Stay indoors or in shade between 12 and 4 pm, drink water or ORS regularly, and check on children and the elderly.",
        "RED": "Extreme heat. Avoid going out, keep cool, drink water or ORS, and get medical help at once for dizziness, confusion or very high fever. Emergency: 112.",
    },
    "hi": {
        "GREEN": "अभी गर्मी की कोई चेतावनी नहीं है।",
        "UNKNOWN": "हमारे स्टेशन से डेटा नहीं आ रहा, इसलिए तापमान की पुष्टि नहीं हो सकती। IMD की जानकारी देखें।",
        "YELLOW": "बहुत गर्मी और उमस है। बार-बार पानी पिएँ, दोपहर में भारी काम से बचें और हल्के कपड़े पहनें।",
        "ORANGE": "भीषण गर्मी है। दोपहर 12 से 4 बजे के बीच घर या छाँव में रहें, पानी या ORS पीते रहें और बच्चों व बुज़ुर्गों का ध्यान रखें।",
        "RED": "अत्यधिक गर्मी है। बाहर जाने से बचें, ठंडी जगह रहें, पानी या ORS पिएँ, और चक्कर, भ्रम या बहुत तेज़ बुखार होने पर तुरंत डॉक्टर को दिखाएँ। आपातकाल: 112।",
    },
}

REASONS = {
    "en": {
        "sensor_offline": "Station has sent no data for {minutes} min",
        "sensor_offline_none": "Station has not sent any data yet",
        "rain_data_missing": "Rain sensor is not reporting",
        "water_level_missing": "Water-level sensor is not reporting",
        "level_above_danger": "River level {level_cm} cm is above the danger mark ({danger_cm} cm)",
        "rapid_rise_saturated_heavy_forecast": "Water rising fast ({rise} cm/h), soil {soil}% wet, heavy rain forecast ({forecast_mm} mm)",
        "rapid_rise_near_danger": "Water rising fast ({rise} cm/h) and already at {percent}% of the danger mark",
        "very_heavy_rain_saturated": "Very heavy rain ({mm} mm in 24 h) on soil that is {soil}% wet",
        "flash_rise": "Water is surging: {rise} cm per hour",
        "upstream_surge_near_danger": "Upstream station: water rising fast ({rise} cm/h) at {percent}% of its danger mark",
        "upstream_surge": "Upstream station: water rising fast ({rise} cm/h) - a surge may reach here",
        "upstream_rising": "Upstream station: water level rising ({rise} cm/h)",
        "rain_24h": "Rain in the last 24 h: {mm} mm",
        "rain_72h": "Rain in the last 72 h: {mm} mm",
        "rain_1h_intense": "Intense rain: {mm} mm in the last hour",
        "level_near_danger_rising": "Water at {percent}% of the danger mark and rising ({rise} cm/h)",
        "level_rising_rapid": "Water level rising fast ({rise} cm/h)",
        "level_rising": "Water level rising ({rise} cm/h)",
        "level_elevated": "Water at {percent}% of the danger mark",
        "forecast_heavy_rain": "Heavy rain forecast: about {mm} mm in the next 24 h",
        "saturated_soil_forecast_rain": "Soil is {soil}% wet and {mm} mm rain is forecast",
        "extreme_heat": "Temperature {temp} C, feels like {hi} C",
        "severe_heat": "Temperature {temp} C, feels like {hi} C",
        "high_heat": "Temperature {temp} C, feels like {hi} C",
        "temperature_missing": "Temperature sensor is not reporting",
    },
    "hi": {
        "sensor_offline": "स्टेशन से {minutes} मिनट से कोई डेटा नहीं आया",
        "sensor_offline_none": "स्टेशन से अभी तक कोई डेटा नहीं आया",
        "rain_data_missing": "वर्षामापी सेंसर से डेटा नहीं आ रहा",
        "water_level_missing": "जलस्तर सेंसर से डेटा नहीं आ रहा",
        "level_above_danger": "नदी का जलस्तर {level_cm} सेमी है, जो ख़तरे के निशान ({danger_cm} सेमी) से ऊपर है",
        "rapid_rise_saturated_heavy_forecast": "पानी तेज़ी से बढ़ रहा है ({rise} सेमी/घंटा), मिट्टी {soil}% गीली है, भारी बारिश का पूर्वानुमान ({forecast_mm} मिमी)",
        "rapid_rise_near_danger": "पानी तेज़ी से बढ़ रहा है ({rise} सेमी/घंटा) और ख़तरे के निशान के {percent}% तक पहुँच चुका है",
        "very_heavy_rain_saturated": "24 घंटे में {mm} मिमी बहुत भारी बारिश, मिट्टी {soil}% गीली",
        "flash_rise": "पानी अचानक बढ़ रहा है: {rise} सेमी प्रति घंटा",
        "upstream_surge_near_danger": "ऊपरी धारा के स्टेशन पर पानी तेज़ी से बढ़ रहा है ({rise} सेमी/घंटा), ख़तरे के निशान का {percent}%",
        "upstream_surge": "ऊपरी धारा के स्टेशन पर पानी तेज़ी से बढ़ रहा है ({rise} सेमी/घंटा) - उछाल यहाँ तक पहुँच सकता है",
        "upstream_rising": "ऊपरी धारा के स्टेशन पर जलस्तर बढ़ रहा है ({rise} सेमी/घंटा)",
        "rain_24h": "पिछले 24 घंटे में बारिश: {mm} मिमी",
        "rain_72h": "पिछले 72 घंटे में बारिश: {mm} मिमी",
        "rain_1h_intense": "तेज़ बारिश: पिछले एक घंटे में {mm} मिमी",
        "level_near_danger_rising": "पानी ख़तरे के निशान के {percent}% पर है और बढ़ रहा है ({rise} सेमी/घंटा)",
        "level_rising_rapid": "जलस्तर तेज़ी से बढ़ रहा है ({rise} सेमी/घंटा)",
        "level_rising": "जलस्तर बढ़ रहा है ({rise} सेमी/घंटा)",
        "level_elevated": "पानी ख़तरे के निशान के {percent}% पर है",
        "forecast_heavy_rain": "भारी बारिश का पूर्वानुमान: अगले 24 घंटे में लगभग {mm} मिमी",
        "saturated_soil_forecast_rain": "मिट्टी {soil}% गीली है और {mm} मिमी बारिश का पूर्वानुमान है",
        "extreme_heat": "तापमान {temp} डिग्री, अनुभूत तापमान {hi} डिग्री",
        "severe_heat": "तापमान {temp} डिग्री, अनुभूत तापमान {hi} डिग्री",
        "high_heat": "तापमान {temp} डिग्री, अनुभूत तापमान {hi} डिग्री",
        "temperature_missing": "तापमान सेंसर से डेटा नहीं आ रहा",
    },
}

CROP_REASONS = {
    "en": {"temp_ok": "temperature {temp} C suits it", "temp_marginal": "temperature {temp} C is a bit off its best range",
           "rain_ok": "expected rain (~{rain} mm) is suitable", "rain_low": "expected rain (~{rain} mm) is low - irrigation needed",
           "rain_high": "expected rain (~{rain} mm) is high - needs good drainage", "needs_irrigation": "rain (~{rain} mm) is not enough - irrigate"},
    "hi": {"temp_ok": "तापमान {temp} डिग्री उपयुक्त है", "temp_marginal": "तापमान {temp} डिग्री सर्वोत्तम सीमा से थोड़ा अलग है",
           "rain_ok": "अपेक्षित बारिश (~{rain} मिमी) उपयुक्त है", "rain_low": "अपेक्षित बारिश (~{rain} मिमी) कम है - सिंचाई चाहिए",
           "rain_high": "अपेक्षित बारिश (~{rain} मिमी) अधिक है - जल निकासी अच्छी चाहिए", "needs_irrigation": "बारिश (~{rain} मिमी) काफ़ी नहीं - सिंचाई करें"},
}

SEASON = {"en": {"kharif": "Kharif", "rabi": "Rabi", "zaid": "Zaid"}, "hi": {"kharif": "खरीफ़", "rabi": "रबी", "zaid": "जायद"}}

TEXT = {
    "en": {
        "welcome": "Namaste! I am MausamSahayak. I share live weather from our field stations, flood and heat advisories, and crop suggestions.\n\nFirst, choose your language.",
        "language_set": "Language set to English.",
        "ask_location": "Please share your location (tap the button below) so I can find the nearest station.",
        "share_location_button": "📍 Share my location",
        "location_saved": "Nearest station: {name}, {km} km away.\n\nYou can ask: 'weather', 'flood risk', 'crop advice'. Use /subscribe to get alerts here.",
        "location_far": "The nearest station ({name}) is {km} km away - too far to give you reliable local readings. I will show you no local data, but you can still follow IMD and CWC. We are adding more stations.",
        "no_stations": "No stations are registered yet.",
        "need_location": "I need your location first.",
        "current_title": "📍 {name} ({km} km away)",
        "temperature": "🌡 Temperature",
        "humidity": "💧 Humidity",
        "rain24": "🌧 Rain, last 24 h",
        "water": "🌊 Water level",
        "soil": "🌱 Soil moisture",
        "updated": "🕒 Updated {age} min ago",
        "no_data_yet": "This station has not sent any data yet.",
        "stale_line": "⚠ Station has not reported for {age} min. Readings above may be old - status is UNKNOWN, not safe.",
        "flood_line": "Flood: {emoji} {label}",
        "heat_line": "Heat: {emoji} {label}",
        "why": "Why:",
        "crop_title": "🌾 Crop suggestions ({season} season, {mode})",
        "mode_rainfed": "rain-fed", "mode_irrigated": "irrigated",
        "crop_none": "No crop fits the current conditions well. Please ask your local agriculture office / KVK.",
        "crop_footer": "These are indicative suggestions from local readings and rainfall normals. Please confirm with your local agriculture office or KVK before sowing.",
        "crop_ask": "Do you have irrigation?", "yes": "Yes, irrigated", "no": "No, rain-fed",
        "no_station_crop": "I cannot give crop advice because there is no station near you yet.",
        "subscribed": "✅ You will get alerts for {name}. Alerts are advisories - always follow your local authorities. Add a phone number for SMS on RED alerts: /phone +91XXXXXXXXXX",
        "unsubscribed": "You will no longer receive alerts. Send /subscribe to turn them back on.",
        "phone_saved": "Phone number saved. You will get an SMS for RED alerts.",
        "phone_invalid": "Please send an Indian mobile number like /phone +919876543210",
        "phone_removed": "Phone number removed.",
        "api_down": "Sorry, I cannot reach the monitoring server right now. Please try again in a few minutes and follow IMD / local authority updates in the meantime.",
        "help": "I can help with:\n• weather - current readings near you\n• flood risk / heat\n• crop advice\n\nCommands: /start /language /location /now /risk /crop /subscribe /unsubscribe /phone /help",
        "unknown": "I did not understand. Try 'weather', 'flood risk' or 'crop advice', or send /help.",
        "disclaimer": "Advisory only. For evacuation orders follow your district administration / State Disaster Management Authority. Emergency: 112.",
        "alert_up": "ALERT for {name}",
        "alert_down": "UPDATE for {name} - risk lowered",
        "flood_word": "Flood", "heat_word": "Heat",
        "sms_flood": "MausamSahayak: FLOOD ALERT (RED) near {name}. Prepare to move to higher ground. Advisory only; follow local authorities. Emergency 112.",
        "sms_heat": "MausamSahayak: EXTREME HEAT (RED) near {name}. Stay indoors, drink water/ORS. Emergency 112.",
    },
    "hi": {
        "welcome": "नमस्ते! मैं मौसमसहायक हूँ। मैं हमारे स्टेशनों से लाइव मौसम, बाढ़ और गर्मी की चेतावनी, और फ़सल सुझाव देता हूँ।\n\nपहले अपनी भाषा चुनें।",
        "language_set": "भाषा हिंदी में सेट हो गई।",
        "ask_location": "कृपया अपनी लोकेशन साझा करें (नीचे बटन दबाएँ) ताकि मैं सबसे नज़दीकी स्टेशन ढूँढ सकूँ।",
        "share_location_button": "📍 मेरी लोकेशन भेजें",
        "location_saved": "सबसे नज़दीकी स्टेशन: {name}, {km} किमी दूर।\n\nआप पूछ सकते हैं: 'मौसम', 'बाढ़', 'फसल सलाह'। अलर्ट पाने के लिए /subscribe भेजें।",
        "location_far": "सबसे नज़दीकी स्टेशन ({name}) {km} किमी दूर है - भरोसेमंद स्थानीय आँकड़े देने के लिए बहुत दूर। आप IMD और CWC की जानकारी देख सकते हैं। हम और स्टेशन जोड़ रहे हैं।",
        "no_stations": "अभी कोई स्टेशन पंजीकृत नहीं है।",
        "need_location": "पहले मुझे आपकी लोकेशन चाहिए।",
        "current_title": "📍 {name} ({km} किमी दूर)",
        "temperature": "🌡 तापमान",
        "humidity": "💧 नमी",
        "rain24": "🌧 पिछले 24 घंटे की बारिश",
        "water": "🌊 जलस्तर",
        "soil": "🌱 मिट्टी की नमी",
        "updated": "🕒 {age} मिनट पहले अपडेट हुआ",
        "no_data_yet": "इस स्टेशन से अभी तक कोई डेटा नहीं आया।",
        "stale_line": "⚠ स्टेशन से {age} मिनट से कोई डेटा नहीं आया। ऊपर के आँकड़े पुराने हो सकते हैं - स्थिति अज्ञात है, सुरक्षित नहीं।",
        "flood_line": "बाढ़: {emoji} {label}",
        "heat_line": "गर्मी: {emoji} {label}",
        "why": "कारण:",
        "crop_title": "🌾 फ़सल सुझाव ({season} मौसम, {mode})",
        "mode_rainfed": "वर्षा आधारित", "mode_irrigated": "सिंचित",
        "crop_none": "मौजूदा हालात में कोई फ़सल ठीक नहीं बैठ रही। कृपया अपने कृषि कार्यालय / KVK से पूछें।",
        "crop_footer": "ये स्थानीय आँकड़ों और सामान्य वर्षा पर आधारित सांकेतिक सुझाव हैं। बुवाई से पहले अपने कृषि कार्यालय या KVK से पुष्टि कर लें।",
        "crop_ask": "क्या आपके पास सिंचाई की सुविधा है?", "yes": "हाँ, सिंचित", "no": "नहीं, वर्षा आधारित",
        "no_station_crop": "आपके पास अभी कोई स्टेशन नहीं है, इसलिए मैं फ़सल सलाह नहीं दे सकता।",
        "subscribed": "✅ अब आपको {name} के अलर्ट मिलेंगे। अलर्ट केवल परामर्श हैं - हमेशा स्थानीय प्रशासन की बात मानें। लाल अलर्ट पर SMS के लिए फ़ोन नंबर जोड़ें: /phone +91XXXXXXXXXX",
        "unsubscribed": "अब आपको अलर्ट नहीं मिलेंगे। फिर से चालू करने के लिए /subscribe भेजें।",
        "phone_saved": "फ़ोन नंबर सेव हो गया। लाल अलर्ट पर आपको SMS मिलेगा।",
        "phone_invalid": "कृपया भारतीय मोबाइल नंबर भेजें, जैसे /phone +919876543210",
        "phone_removed": "फ़ोन नंबर हटा दिया गया।",
        "api_down": "क्षमा करें, अभी मॉनिटरिंग सर्वर से संपर्क नहीं हो पा रहा। कुछ मिनट बाद फिर कोशिश करें और तब तक IMD / स्थानीय प्रशासन की सूचनाएँ देखें।",
        "help": "मैं इनमें मदद कर सकता हूँ:\n• मौसम - आपके पास का ताज़ा हाल\n• बाढ़ / गर्मी का जोखिम\n• फ़सल सलाह\n\nकमांड: /start /language /location /now /risk /crop /subscribe /unsubscribe /phone /help",
        "unknown": "मैं समझ नहीं पाया। 'मौसम', 'बाढ़' या 'फसल सलाह' लिखें, या /help भेजें।",
        "disclaimer": "यह केवल परामर्श है। निकासी के आदेश के लिए अपने ज़िला प्रशासन / राज्य आपदा प्रबंधन प्राधिकरण की बात मानें। आपातकाल: 112।",
        "alert_up": "{name} के लिए अलर्ट",
        "alert_down": "{name} के लिए अपडेट - जोखिम घटा",
        "flood_word": "बाढ़", "heat_word": "गर्मी",
        "sms_flood": "मौसमसहायक: {name} के पास बाढ़ का लाल अलर्ट। ऊँची जगह जाने की तैयारी करें। यह केवल परामर्श है; प्रशासन की बात मानें। आपातकाल 112।",
        "sms_heat": "मौसमसहायक: {name} के पास अत्यधिक गर्मी (लाल)। घर में रहें, पानी/ORS पिएँ। आपातकाल 112।",
    },
}

LANGS = ("en", "hi")


def norm_lang(lang):
    return lang if lang in LANGS else "en"


def t(lang, key, **kw):
    lang = norm_lang(lang)
    s = TEXT[lang].get(key) or TEXT["en"][key]
    return s.format(**kw) if kw else s
