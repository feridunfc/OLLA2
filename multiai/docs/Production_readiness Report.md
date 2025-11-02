# MultiAI Enterprise – v4.9 Roadmap
**Tarih:** 2025-10-30  
**Durum:** 4.9-prep  
**Kaynak:** Mimari4 özet ve yol haritası + multiai/ kodu

## 1. Amaç
v4.8’de deterministik manifest, basic ledger ve Docker sandbox PoC’i eklendi.  
v4.9’un amacı bunları “kurumsal üretime yakın” hâle getirmek:
- Sandbox’ı her subprocess için zorunlu kılmak,
- Ledger kayıtlarını imzalamak,
- Auto-patch’i insan onayına bağlamak,
- Observability’yi açmak,
- n8n approval / debug loop’u tamamlamak.

---

## 2. Sprint’ler

### 🅰 Sprint-A — Ledger & Determinism (Takviye)
- [x] Manifest’ler hash’lenip SQLite ledger’a yazılıyor.
- [ ] Hash’ler **imzalanacak** (örn. GPG veya cosign).
- [ ] Ledger entry’leri `manifest_id`, `sprint`, `created_at`, `signature` alanlarını içerecek.
- [ ] `scripts/write_ledger.py` ve `scripts/compare_manifest.py` imzalı moda çekilecek.

**Kabul Kriteri:** Aynı manifest için aynı hash, imzalı olarak tekrar üretilebilmeli.

---

### 🅱 Sprint-B — Secure Sandbox (Enforcement)
- [x] `multiai/utils/secure_sandbox_docker.py` ile Docker tabanlı güvenli koşum PoC’i var.
- [ ] Tüm **subprocess / test / patch** çağrıları bu sandbox üzerinden zorunlu geçecek.
- [ ] Non-root user, seccomp profili ve `no-new-privileges` default’a alınacak.
- [ ] Sandbox dışından çağrı tespit edilirse task fail edecek ve supervisor’a rapor atacak.

**Kabul Kriteri:** Agent’ların çalıştırdığı hiçbir komut host’ta doğrudan koşamamalı.

---

### 🅲 Sprint-C — BudgetGuard + PolicyAgent (Genişletme)
- [x] Temel bütçe rezervasyonu var.
- [ ] `config/policy.yaml` içinde **agent-bazlı limitler**: `coder.max_tokens`, `researcher.max_cloud_calls`, `tester.max_runtime` vb.
- [ ] Limit aşıldığında otomatik **local LLM fallback**.
- [ ] Policy ihlali olduğunda supervisor’a ve n8n’e event gönderilecek.

**Kabul Kriteri:** İhlal → cloud çağrısı bloklanır, local model denenir, olay loglanır.

---

### 🅳 Sprint-D — Critic & Auto-Patch Flow
- [x] `multiai/agents/critic_agent.py` LLM tabanlı patch önerisi üretiyor.
- [ ] Patch’ler **doğrudan uygulanmayacak**, önce human approval isteyecek.
- [ ] `scripts/file_patcher.py` için **dry-run modu** eklenecek.
- [ ] n8n workflow’unda “Apply Patch?” adımı eklenecek.
- [ ] PolicyAgent “auto_patch: allowed: false” ise işlem bloklanacak.

**Kabul Kriteri:** İnsan onayı olmadan tek satır kod bile değişmemeli.

---

### 🅴 Sprint-E — Observability & Monitoring
- [ ] `multiai/api/metrics.py` Prometheus endpoint’i stabilize edilecek.
- [ ] `utils/observability.py` ile OpenTelemetry span’leri eklenecek.
- [ ] Temel Grafana dashboard JSON’u repoya konacak.
- [ ] Alarm kuralları: 
  - `budget_spent > threshold`
  - `agent_error_rate > X`
  - `sandbox_violation > 0`

**Kabul Kriteri:** En az 1 dashboard + 2 alert kuralı çalışır durumda.

---

### 🅵 Sprint-F — n8n + Automation
- [ ] Approval ve debug loop otomasyonu eklenecek.
- [ ] FastAPI tarafında:
  - `POST /api/approval/{sprint_id}`
  - `POST /api/sprint/run_tests`
- [ ] n8n ManualApproval node’u patch ve yüksek riskli değişiklikler için zorunlu olacak.
- [ ] Onay gelince supervisor task’i devam ettirecek.

**Kabul Kriteri:** n8n’den “approve” gelmeden sistem kritik adımı çalıştırmıyor olacak.

---

## 3. Kritik Eksikler (Devam Edenler)
1. **Sandbox Enforcement:** Bütün subprocess’ler Docker sandbox içinde.  
2. **Ledger Signature:** Manifest hash’i imzalı olarak ledger’a yazılacak.  
3. **Observability:** Prometheus + OTel tamamlanacak.  
4. **Auto-patch Güvenliği:** Critic önerisi → insan onayı → sonra patch.  
5. **PolicyAgent:** YAML tabanlı politika yönetimi genişletilecek.
---

## 4. Mimari İlke Seti
1. **Fail-safe first** — Bütçe / sandbox / policy hata verirse sistem fallback eder.
2. **Deterministic outputs** — Aynı girdi aynı çıktıyı üretir, ledger’da izi olur.
3. **Human oversight** — Kritik adımlar insan onayı olmadan ilerlemez.
4. **Cost-aware orchestration** — Cloud pahalı → önce limite bak, sonra çağır.
5. **Transparent observability** — Her agent çağrısı ölçülür ve dashboard’da görünür.

---

## 5. Teslim Formatı
- `multiai/` (core kod)
- `docs/ROADMAP_v4.9.md` (bu dosya)
- `n8n_workflow_v4.9.json` (approval + debug loop)
- `config/policy.yaml` (güçlendirilmiş)
