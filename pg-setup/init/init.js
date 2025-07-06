db = db.getSiblingDB("meli_db");

const collections = [
  "products",
  "Q&A",
  "conversations",
  "user_search_history",
  "recommendation_logs",
  "campaigns"
];

collections.forEach(name => {
  if (!db.getCollectionNames().includes(name)) {
    db.createCollection(name);
    print(`Colección '${name}' creada.`);
  } else {
    print(`ℹColección '${name}' ya existe.`);
  }
});