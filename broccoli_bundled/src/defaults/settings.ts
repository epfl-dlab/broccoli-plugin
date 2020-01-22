export interface settingsInterface {
    language_id: string,
    min_dist: number,
    threshold : number,
    only_neural: boolean,
    filter_stopwords: boolean,
    show_riddle: boolean
}

export var default_settings: settingsInterface = {
    // language related settings
    language_id: 'fr',  // the language you want to learn
    min_dist: 30,       // min distance between Broccoli words
    threshold : 0.0,    // min probability for Broccoli words
    only_neural: true,  // use only neural language model (no additional regression on top of lm features)
    filter_stopwords: true,

    // UI related settings
    show_riddle: false
}