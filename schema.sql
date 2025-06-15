PRAGMA foreign_keys = ON;
-- Tarixiy obidalar uchun jadval
CREATE TABLE IF NOT EXISTS obidalar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nomi TEXT NOT NULL,
    tiklangan_yili TEXT,
    manzili TEXT,
    qurilish_materiallari TEXT,
    bosh_fasadi TEXT,
    olchamlari TEXT,
    tarixiy_malumot TEXT,
    texnik_holati TEXT,
    guruh TEXT CHECK(guruh IN ('Restavratsiyalangan', 'Restavratsiya kutilayotgan')),
    turi TEXT CHECK(turi IN ('Paxsa', 'Gil')),
    rasm_url TEXT,
    yaratilgan_sana TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    yangilangan_sana TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_superadmin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Obidalar rasmlari uchun jadval
CREATE TABLE IF NOT EXISTS obida_rasmlar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    obida_id INTEGER NOT NULL,
    rasm_url TEXT NOT NULL,
    asosiy BOOLEAN DEFAULT 0,
    izoh TEXT,
    FOREIGN KEY (obida_id) REFERENCES obidalar (id) ON DELETE CASCADE
);

-- Foydalanuvchilar xabarlari uchun jadval
CREATE TABLE IF NOT EXISTS xabarlar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ism TEXT NOT NULL,
    email TEXT NOT NULL,
    telefon TEXT,
    mavzu TEXT NOT NULL,
    xabar TEXT NOT NULL,
    oqilgan BOOLEAN DEFAULT 0,
    yuborilgan_sana TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Misol uchun ma'lumotlar - APOSTROFLARNI '' SIFATIDA BELGILAYMIZ
INSERT INTO obidalar (nomi, tiklangan_yili, manzili, qurilish_materiallari, bosh_fasadi, olchamlari, tarixiy_malumot, texnik_holati, guruh, turi, rasm_url)
VALUES ('Registon maydoni', 'XV asr', 'Samarqand shahri, O''zbekiston', 'G''isht, marmar, koshin', 'Uchta madrasa va keng maydondan iborat', '120x90 metr', 'XV asrda Ulug''bek tomonidan barpo etilgan', 'A''lo darajada restavratsiya qilingan', 'Restavratsiyalangan', 'Gil', '/static/images/registon.jpg');

INSERT INTO obidalar (nomi, tiklangan_yili, manzili, qurilish_materiallari, bosh_fasadi, olchamlari, tarixiy_malumot, texnik_holati, guruh, turi, rasm_url)
VALUES ('Ark qal''asi', 'V asr', 'Buxoro shahri, O''zbekiston', 'Paxsa, xom g''isht', 'Baland devorlar va darvozalar', '130x130 metr', 'V asrda qurilgan, Buxoro amirligi qarorgohi', 'Yaxshi holatda', 'Restavratsiyalangan', 'Paxsa', '/static/images/ark.jpg');

INSERT INTO obidalar (nomi, tiklangan_yili, manzili, qurilish_materiallari, bosh_fasadi, olchamlari, tarixiy_malumot, texnik_holati, guruh, turi, rasm_url)
VALUES ('Ko''hna Urganch', 'X-XIV asr', 'Xorazm viloyati, O''zbekiston', 'Paxsa, pishiq g''isht', 'Qadimiy shahar qoldiqlari', '200 gektardan ortiq', 'X-XIV asrlarda rivojlangan Xorazm poytaxti', 'Restavratsiya talab qiladi', 'Restavratsiya kutilayotgan', 'Paxsa', '/static/images/urgench.jpg');

INSERT INTO obidalar (nomi, tiklangan_yili, manzili, qurilish_materiallari, bosh_fasadi, olchamlari, tarixiy_malumot, texnik_holati, guruh, turi, rasm_url)
VALUES ('Ayoz qal''a', 'II asr', 'Qoraqalpog''iston, O''zbekiston', 'Paxsa', 'To''rtburchak shaklida, burjlar bilan', '180x150 metr', 'II asrda qurilgan, Xorazm mudofaa tizimi', 'Qisman buzilgan', 'Restavratsiya kutilayotgan', 'Paxsa', '/static/images/ayoz.jpg');

INSERT INTO obidalar (nomi, tiklangan_yili, manzili, qurilish_materiallari, bosh_fasadi, olchamlari, tarixiy_malumot, texnik_holati, guruh, turi, rasm_url)
VALUES ('Shoxizinda majmuasi', 'XI-XV asr', 'Samarqand shahri, O''zbekiston', 'Pishiq g''isht, koshin, marmar', 'Maqbaralar ansambli', '100 metr uzunlikda', 'XI-XV asrlarda shakllangan, 20dan ortiq maqbara', 'A''lo darajada restavratsiya qilingan', 'Restavratsiyalangan', 'Gil', '/static/images/shoxizinda.jpg');