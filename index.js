const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');
const app = express();

// 1. CONNEXION À LA BASE POSTGRESQL (SUPABASE)
const connectionString = process.env.DATABASE_URL || 'postgresql://postgres.xtalrmoacijdwioazfps:UWrqR&jzVQp9U$r@aws-0-eu-west-1.pooler.supabase.com:6543/postgres';

const pool = new Pool({
  connectionString: connectionString,
  ssl: {
    rejectUnauthorized: false // Nécessaire pour les connexions distantes comme Supabase/Railway
  }
});

// 2. CONFIGURATION CORS (Pour ton site Vercel)
app.use(cors({
  origin: 'https://qr-web-dbap.vercel.app',
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json());

// 3. REGISTRE DES AUTORITÉS (Codes secrets pour Ambulance/Police)
const authorityRegistry = [
  { code: "SAMU-228", type: "ambulance", name: "SAMU Lomé" },
  { code: "POL-CENTRAL", type: "police", name: "Commissariat Central de Lomé" }
];

// 4. ROUTE DE VÉRIFICATION ET RÉCUPÉRATION DES VRAIES DONNÉES
app.post('/api/profile/scan/verify', async (req, res) => {
  const { token, pin, authority_type } = req.body;

  // A. Vérification du code de l'intervenant
  const authority = authorityRegistry.find(a => a.code === pin && a.type === authority_type);
  if (!authority) {
    return res.status(401).json({ message: "Code d'identification invalide." });
  }

  try {
    // B. Requête SQL pour récupérer les vraies données de l'utilisateur
    // J'utilise les noms de colonnes standards, ajuste-les si nécessaire
    const query = `
      SELECT first_name, last_name, blood_type, allergies, medical_conditions, emergency_contact 
      FROM users 
      WHERE qr_token = $1
    `;
    const result = await pool.query(query, [token]);

    if (result.rows.length === 0) {
      return res.status(404).json({ message: "Aucun profil trouvé pour ce QR Code." });
    }

    const user = result.rows[0];

    // C. Envoi des vraies données au site Web
    res.json({
      identity: {
        first_name: user.first_name,
        last_name: user.last_name
      },
      medical: {
        blood_type: user.blood_type,
        allergies: user.allergies,
        conditions: user.medical_conditions
      },
      emergency_contact: user.emergency_contact,
      audit: {
        verified_by: authority.name,
        date: new Date().toLocaleString('fr-FR')
      }
    });

  } catch (err) {
    console.error("Erreur Database:", err);
    res.status(500).json({ message: "Erreur lors de la lecture des données réelles sur Supabase." });
  }
});

// 5. TEST DE CONNEXION
app.get('/health', async (req, res) => {
  try {
    await pool.query('SELECT NOW()');
    res.json({ status: "Connecté à PostgreSQL Supabase ✅" });
  } catch (err) {
    res.status(500).json({ status: "Erreur de connexion DB ❌", details: err.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Serveur SafeLife en ligne sur le port ${PORT}`);
});