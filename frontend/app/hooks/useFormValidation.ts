'use client';

import { useState, useCallback } from 'react';

// Tipos de validação
type ValidationRule = {
    required?: boolean;
    minLength?: number;
    maxLength?: number;
    pattern?: RegExp;
    custom?: (value: string) => boolean;
    message: string;
};

type FieldValidation = {
    [fieldName: string]: ValidationRule[];
};

type ValidationErrors = {
    [fieldName: string]: string | null;
};

type ValidationResult = {
    isValid: boolean;
    errors: ValidationErrors;
};

export function useFormValidation(rules: FieldValidation) {
    const [errors, setErrors] = useState<ValidationErrors>({});
    const [touched, setTouched] = useState<{ [key: string]: boolean }>({});

    // Valida um campo específico
    const validateField = useCallback((fieldName: string, value: string): string | null => {
        const fieldRules = rules[fieldName];
        if (!fieldRules) return null;

        for (const rule of fieldRules) {
            // Required
            if (rule.required && (!value || value.trim() === '')) {
                return rule.message;
            }

            // Min length
            if (rule.minLength && value.length < rule.minLength) {
                return rule.message;
            }

            // Max length
            if (rule.maxLength && value.length > rule.maxLength) {
                return rule.message;
            }

            // Pattern (regex)
            if (rule.pattern && !rule.pattern.test(value)) {
                return rule.message;
            }

            // Custom validation
            if (rule.custom && !rule.custom(value)) {
                return rule.message;
            }
        }

        return null;
    }, [rules]);

    // Valida e atualiza estado
    const validate = useCallback((fieldName: string, value: string) => {
        const error = validateField(fieldName, value);
        setErrors(prev => ({ ...prev, [fieldName]: error }));
        return error === null;
    }, [validateField]);

    // Marca campo como tocado (para mostrar erros só depois de interação)
    const touch = useCallback((fieldName: string) => {
        setTouched(prev => ({ ...prev, [fieldName]: true }));
    }, []);

    // Valida todos os campos de uma vez
    const validateAll = useCallback((values: { [key: string]: string }): ValidationResult => {
        const newErrors: ValidationErrors = {};
        let isValid = true;

        for (const fieldName of Object.keys(rules)) {
            const error = validateField(fieldName, values[fieldName] || '');
            newErrors[fieldName] = error;
            if (error) isValid = false;
        }

        setErrors(newErrors);
        setTouched(Object.keys(rules).reduce((acc, key) => ({ ...acc, [key]: true }), {}));

        return { isValid, errors: newErrors };
    }, [rules, validateField]);

    // Limpa erros
    const clearErrors = useCallback(() => {
        setErrors({});
        setTouched({});
    }, []);

    // Retorna erro só se campo foi tocado
    const getError = useCallback((fieldName: string): string | null => {
        return touched[fieldName] ? errors[fieldName] : null;
    }, [errors, touched]);

    return {
        errors,
        touched,
        validate,
        touch,
        validateAll,
        clearErrors,
        getError,
    };
}

// Exemplo de uso:
// const { validate, getError, validateAll } = useFormValidation({
//   caption: [
//     { required: true, message: 'Caption é obrigatório' },
//     { maxLength: 2200, message: 'Máximo 2200 caracteres' },
//   ],
//   scheduleDate: [
//     { required: true, message: 'Data é obrigatória' },
//     { custom: (v) => new Date(v) > new Date(), message: 'Data deve ser futura' },
//   ],
// });
