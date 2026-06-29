/**
 * Password strength meter component.
 * Показывает визуальный индикатор надёжности пароля в реальном времени.
 */

interface Props {
  password: string;
  minLength?: number;
  requireUpper?: boolean;
  requireSpecial?: boolean;
}

interface Check { label: string; ok: boolean; }

function getChecks(password: string, props: Props): Check[] {
  return [
    { label: `Минимум ${props.minLength ?? 8} символов`, ok: password.length >= (props.minLength ?? 8) },
    { label: "Содержит букву",  ok: /[A-Za-z]/.test(password) },
    { label: "Содержит цифру",  ok: /\d/.test(password) },
    ...(props.requireUpper  ? [{ label: "Заглавная буква", ok: /[A-Z]/.test(password) }] : []),
    ...(props.requireSpecial ? [{ label: "Спецсимвол (!@#…)", ok: /[!@#$%^&*]/.test(password) }] : []),
  ];
}

function getStrength(checks: Check[]): { level: number; label: string; color: string } {
  const passed = checks.filter(c => c.ok).length;
  const ratio  = checks.length ? passed / checks.length : 0;
  if (ratio === 1)   return { level: 4, label: "Отлично",  color: "bg-green-500"  };
  if (ratio >= 0.75) return { level: 3, label: "Хорошо",   color: "bg-blue-500"   };
  if (ratio >= 0.5)  return { level: 2, label: "Средний",  color: "bg-amber-500"  };
  if (ratio > 0)     return { level: 1, label: "Слабый",   color: "bg-red-500"    };
  return                    { level: 0, label: "",          color: "bg-gray-200"   };
}

export function PasswordStrength({ password, minLength, requireUpper, requireSpecial }: Props) {
  if (!password) return null;

  const checks   = getChecks(password, { password, minLength, requireUpper, requireSpecial });
  const strength = getStrength(checks);

  return (
    <div className="mt-2 space-y-2">
      {/* Bar */}
      <div className="flex gap-1">
        {[1, 2, 3, 4].map(n => (
          <div
            key={n}
            className={`h-1.5 flex-1 rounded-full transition-colors duration-300 ${
              n <= strength.level ? strength.color : "bg-gray-200 dark:bg-gray-600"
            }`}
          />
        ))}
      </div>
      {strength.label && (
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Надёжность: <span className="font-medium">{strength.label}</span>
        </p>
      )}
      {/* Checklist */}
      <ul className="space-y-0.5">
        {checks.map(c => (
          <li key={c.label} className={`flex items-center gap-1.5 text-xs ${c.ok ? "text-green-600 dark:text-green-400" : "text-gray-400"}`}>
            <span>{c.ok ? "✓" : "○"}</span>
            {c.label}
          </li>
        ))}
      </ul>
    </div>
  );
}
