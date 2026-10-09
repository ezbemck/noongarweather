# AI Assistance Log (AI-LOG.md)

This log documents significant AI-assisted development, design iterations, troubleshooting, and testing for the Noongar Weather Streamlit educational application.

## Summary of AI Contribution
- **Backend Architecture**: Implemented robust data ingestion for BoM weather records (1993–2026), cleaning pipelines, modular season mapping (`season_mapper.py`), and statistical summary helpers (`aggregations.py`).
- **Interactive Features**: Built the dynamic Birthday Explorer card with seasonal data, custom flower imagery, and CSS `@keyframes popIn` animations.
- **Mobile Responsiveness & Polish**: Resolved mobile layout quirks using fluid CSS sizing (`clamp`) and touch-friendly navigation styles.
- **Data Governance & Testing**: Structured species metadata (`species_info.json`, `seasons.json`) against verified cultural and meteorological sources, compiled complete Wikimedia Commons image attributions, and aligned backend outputs with unit test suites.

---

## Chronological Development Log


### Phase 1: Backend Data Pipeline & Aggregations
- **Task**: Load multi-year BoM weather CSVs, normalize dates, safely handle missing values, and map records to the six Noongar seasons.
- **AI Action**: Guided the creation of data processing scripts, added robust date/season validation, and implemented unrounded floating-point calculations for period extremes (`get_period_extremes`) to ensure unit test compliance.

### Phase 2: Initial Application Draft
- **Task**: Create the first working version of the Noongar Weather educational application.
- **AI Action**:
  - Assisted extensively with generating the initial Streamlit application code and overall structure.
  - The first draft contained four main screens: Home, Past Data, Learn About the Seasons, and a placeholder fourth page.
  - Helped create the main navigation buttons/tabs and organise the application into separate views.
  - Generated much of the initial Home page and Past Data interface.
  - Assisted with creating dropdown controls for exploring historical weather data.
  - Helped generate the code for the two interactive graphs on the Past Data page, including filtering and displaying the selected weather data.
  - Assisted with the initial layout and content structure of the Seasons page.
  - The generated code was subsequently reviewed, run, tested, modified, debugged, and expanded throughout development.

### Phase 3: Global Aesthetic & Birthday Explorer
- **Task**: Overhaul the visual identity to suit a primary school student audience, centering elements and introducing a personalized birthday weather lookup tool.
- **AI Action**: 
  - Styled global containers with soft drop-shadows and generous rounded corners.
  - Built the Birthday Explorer widget with dropdown filters, input validation bounds (1993–2026), base64 local image encoding, and celebratory pop-in animations.
  - Centered navigation tabs and resolved Markdown indentation bugs that caused raw HTML text blocks to render improperly.

### Phase 4: Live Weather Integration & Mobile Responsiveness
- **Task**: Add a live Perth weather feed to the Home tab and ensure the app displays correctly on mobile devices.
- **AI Action**:
  - Integrated the Open-Meteo API to fetch real-time Perth temperature and weather conditions, paired with clear timestamps.
  - Adjusted top branding elements using CSS `clamp()` and flexbox centering to eliminate word-wrapping issues on mobile screens.
  - Fixed mobile tab scrolling behavior to ensure navigation items remain fully accessible.

### Phase 5: Educational Content, Image Credits & Deployment
- **Task**: Structure species data, compile image attributions, and prepare the repository for live cloud deployment.
- **AI Action**:
  - Populated rich species and seasonal metadata mapped to official cultural and environmental sources (BoM Indigenous Weather Knowledge, Noongar Boodjar Language Centre, SWALSC).
  - Added a comprehensive Image Credits section detailing Wikimedia Commons attribution rules, authors, titles, and direct licensing URLs.
  - Created the deployment configuration (`requirements.txt`) and documented continuous delivery steps for Streamlit Community Cloud.