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



db.conversations.createIndex({ region: 1 });
db.conversations.createIndex({ order_id: 1 });                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
db.conversations.createIndex({ store_id: 1 });
db.conversations.createIndex({ user_id: 1 });                    

db.products.createIndex({ region: 1 });

db.user_search_history.createIndex({ region: 1 });