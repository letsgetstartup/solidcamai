import React, { createContext, useContext, useState, useEffect } from 'react';
import en from '../locales/en.json';
import he from '../locales/he.json';

type Locale = 'en' | 'he';
const translations = { en, he };

interface TranslationContextType {
    locale: Locale;
    setLocale: (l: Locale) => void;
    t: (key: string) => string;
    dir: 'ltr' | 'rtl';
}

const TranslationContext = createContext<TranslationContextType | undefined>(undefined);

export const TranslationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [locale, setLocale] = useState<Locale>('en');

    const t = (key: string) => {
        return (translations[locale] as any)[key] || key;
    };

    const dir = translations[locale].__direction as 'ltr' | 'rtl';

    return (
        <TranslationContext.Provider value={{ locale, setLocale, t, dir }}>
            <div dir={dir} className={dir}>
                {children}
            </div>
        </TranslationContext.Provider>
    );
};

export const useTranslation = () => {
    const context = useContext(TranslationContext);
    if (!context) throw new Error("useTranslation must be used within TranslationProvider");
    return context;
};
