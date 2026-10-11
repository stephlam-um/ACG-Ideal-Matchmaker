export function addPreference(draft, trait) {
  if (draft.includes(trait)) return draft;
  const next = draft.trim() ? `${draft.trim()}；${trait}` : trait;
  return next.length <= 2000 ? next : draft;
}

export function filterCharacters(characters, {query = '', series = '', favoritesOnly = false, favorites = new Set()} = {}) {
  const needle = query.trim().normalize('NFKC').toLocaleLowerCase();
  return characters.filter(c => (!series || c.series === series)
    && (!favoritesOnly || favorites.has(c.id))
    && `${c.display_name || c.name} ${c.name} ${c.series} ${c.moe_traits.join(' ')}`.normalize('NFKC').toLocaleLowerCase().includes(needle));
}
