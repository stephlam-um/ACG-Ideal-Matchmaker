import {addPreference, filterCharacters} from './interaction.mjs';
const $ = id => document.getElementById(id);
const examples = {'冷靜但溫柔':'我喜歡外表冷靜、內心溫柔的人，會默默照顧朋友，偶爾害羞，有反差萌。','可靠的夥伴':'我喜歡可靠、有正義感、有幽默感的夥伴，遇到困難會勇敢站出來。','元氣與好奇心':'我喜歡開朗有活力、好奇心旺盛的人，有自己的熱愛，也願意一起嘗試新事物。'};
let result, controller, catalog = [], pageSize = 12, previousDraft = '';
let favorites = new Set();
function readSession(key, fallback) {try {return JSON.parse(sessionStorage.getItem(key)) ?? fallback;} catch {return fallback;}}
function saveSession(key, value) {try {sessionStorage.setItem(key, JSON.stringify(value));} catch { /* Browsing still works when storage is unavailable. */ }}
favorites = new Set(readSession('acg-favorites', []).filter(Number.isInteger));
$('description').value = String(readSession('acg-draft', '')).slice(0, 2000);
function updateDraft() {
  $('character-count').textContent = `${$('description').value.length} / 2000`;
  saveSession('acg-draft', $('description').value);
  for (const button of $('preferences').children) button.setAttribute('aria-pressed', String($('description').value.includes(button.textContent)));
}
function changeDraft(value) {previousDraft = $('description').value; $('description').value = value; $('undo').hidden = previousDraft === value; updateDraft();}
function scrollTo(element) {element.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block:'start'});}
$('description').addEventListener('input', updateDraft);
$('inspiration').addEventListener('change', e => {if (examples[e.target.value]) changeDraft(examples[e.target.value]);});
$('undo').addEventListener('click', () => {changeDraft(previousDraft); $('undo').hidden = true;});
$('clear').addEventListener('click', () => {changeDraft(''); $('inspiration').value = ''; $('description').focus();});
for (const trait of ['溫柔','冷靜','開朗','毒舌','可靠','好奇心','照顧同伴','反差萌']) {
  const button = document.createElement('button'); button.type = 'button'; button.className = 'preference'; button.textContent = trait;
  button.addEventListener('click', () => {changeDraft(addPreference($('description').value, trait)); $('description').focus();});
  $('preferences').append(button);
}
updateDraft();
function tags(container, items) {
  container.replaceChildren();
  for (const item of items) {const tag = document.createElement('span'); tag.className = 'tag'; tag.textContent = item; container.append(tag);}
}
function cards(container, matches, preview = false) {
  container.replaceChildren();
  for (const [i, match] of matches.entries()) {
    const character = preview ? match : match.character;
    const card = document.createElement('article'); card.className = 'card';
    const top = document.createElement('div'); top.className = 'card-top';
    const rank = document.createElement('div'); rank.className = 'rank'; rank.textContent = preview ? 'CHARACTER FILE' : `MATCH / ${String(i+1).padStart(2,'0')} · ${match.score.toFixed(1)}`;
    const favorite = document.createElement('button'); favorite.type = 'button'; favorite.className = 'favorite';
    const sync = () => {const saved = favorites.has(character.id); favorite.textContent = saved ? '★ 已收藏' : '☆ 收藏'; favorite.setAttribute('aria-pressed', String(saved)); favorite.setAttribute('aria-label', `${saved ? '取消收藏' : '收藏'}${character.display_name || character.name}`);}; sync();
    favorite.addEventListener('click', () => {favorites.has(character.id) ? favorites.delete(character.id) : favorites.add(character.id); saveSession('acg-favorites', [...favorites]); renderCatalog(); if (result) cards($('matches'), result.matches);});
    top.append(rank, favorite);
    const name = document.createElement('h3'); name.textContent = character.display_name || character.name;
    const series = document.createElement('p'); series.className = 'series'; series.textContent = character.series || '原始角色檔案';
    const chips = document.createElement('div'); chips.className = 'tags'; tags(chips, character.moe_traits.slice(0, 5));
    const details = document.createElement('details'); const summary = document.createElement('summary'); summary.textContent = '查看完整特質';
    const allTags = document.createElement('div'); allTags.className = 'tags detail-tags'; tags(allTags, character.moe_traits); details.append(summary, allTags);
    if (character.source_url?.startsWith('https://')) {const source = document.createElement('a'); source.href = character.source_url; source.target = '_blank'; source.rel = 'noopener noreferrer'; source.className = 'source-link'; source.textContent = '官方角色介紹 ↗'; details.append(source);}
    else {const origin = document.createElement('p'); origin.className = 'note'; origin.textContent = '原始萌娘百科特質，可能含劇情資訊。'; details.append(origin);}
    card.append(top, name, series, chips, details); container.append(card);
  }
}
function renderCatalog() {
  const filtered = filterCharacters(catalog, {query:$('catalog-search').value, series:$('series-filter').value, favoritesOnly:$('favorites-only').checked, favorites});
  $('catalog-summary').textContent = `${filtered.length} 位角色${$('favorites-only').checked ? ' · 本分頁收藏' : ''}`;
  cards($('characters'), filtered.slice(0, pageSize), true);
  $('catalog-empty').hidden = filtered.length > 0;
  $('load-more').hidden = filtered.length <= pageSize;
}
for (const id of ['catalog-search','series-filter','favorites-only']) $(id).addEventListener('input', () => {pageSize = 12; renderCatalog();});
$('load-more').addEventListener('click', () => {pageSize += 12; renderCatalog();});
try {
  const response = await fetch('/api/catalog'); if (!response.ok) throw new Error();
  const data = await response.json(); catalog = data.characters;
  $('catalog-count').textContent = `角色檔案 · ${data.count} 位`;
  for (const series of [...new Set(catalog.map(c => c.series).filter(Boolean))].sort()) {const option = document.createElement('option'); option.value = series; option.textContent = series; $('series-filter').append(option);}
  renderCatalog();
  if (!data.configured) $('status').textContent = '角色檔案已準備好；管理者尚未設定線上 AI 金鑰。';
} catch {$('catalog-summary').textContent = '角色庫暫時無法載入，請重新整理。';}
$('refine').addEventListener('click', () => {scrollTo($('match-form')); $('description').focus({preventScroll:true});});
$('cancel').addEventListener('click', () => controller?.abort());
$('match-form').addEventListener('submit', async event => {
  event.preventDefault(); if (controller) return;
  controller = new AbortController(); $('error').hidden = true; $('submit').disabled = true; $('submit').textContent = '探索中…'; $('cancel').hidden = false; $('match-form').setAttribute('aria-busy','true');
  $('status').textContent = '正在分析你的偏好並比對角色。可繼續瀏覽角色庫；完成後會顯示結果。';
  try {
    const response = await fetch('/api/match', {method:'POST', signal:controller.signal, headers:{'Content-Type':'application/json'}, body:JSON.stringify({description:$('description').value, k:Number($('count').value)})});
    const data = await response.json(); if (!response.ok) throw new Error(data.error || '匹配暫時無法完成，請重試。');
    result = data; $('query-caption').textContent = '本次偏好：' + data.description; tags($('query-traits'), data.traits); cards($('matches'), data.matches);
    $('report').textContent = data.report || data.reportError; $('results').hidden = false; $('status').textContent = `探索完成，找到 ${data.matches.length} 位角色。可以收藏、展開特質，或修改偏好再試。`; scrollTo($('results'));
  } catch (error) {
    if (error.name === 'AbortError') $('status').textContent = '已停止等待，可修改偏好後再探索。';
    else {$('error').textContent = error.message || '連線失敗，請重試。'; $('error').hidden = false; $('status').textContent = '';}
  } finally {controller = undefined; $('submit').disabled = false; $('submit').textContent = '尋找我的理想型 →'; $('cancel').hidden = true; $('match-form').setAttribute('aria-busy','false');}
});
$('download').addEventListener('click', () => {
  if (!result) return; const url = URL.createObjectURL(new Blob([JSON.stringify(result,null,2)], {type:'application/json'}));
  const a = document.createElement('a'); a.href = url; a.download = 'acg-matches.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
