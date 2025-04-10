-- Table principale pour les applications
CREATE TABLE applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    rda VARCHAR(255) NOT NULL,
    possession DATE,
    type_app VARCHAR(50) NOT NULL,
    hosting VARCHAR(50) NOT NULL,
    criticite TINYINT NOT NULL,
    disponibilite VARCHAR(2) NOT NULL,
    integrite VARCHAR(2) NOT NULL,
    confidentialite VARCHAR(2) NOT NULL,
    perennite VARCHAR(2) NOT NULL,
    score INT DEFAULT NULL,
    answered_questions INT DEFAULT NULL,
    last_evaluation DATETIME DEFAULT NULL,
    responses JSON,
    comments JSON,
    evaluator_name VARCHAR(255),
    UNIQUE(name)  -- Facultatif, si le nom de l'application doit être unique
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table pour l'historique des évaluations
CREATE TABLE evaluations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    score INT NOT NULL,
    answered_questions INT NOT NULL,
    last_evaluation DATETIME NOT NULL,
    evaluator_name VARCHAR(255) NOT NULL,
    responses JSON,
    comments JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
