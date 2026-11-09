-- Ref: New Zealand Electoral Act 1993, Section 191
-- https://www.legislation.govt.nz/act/public/1993/0087/latest/DLM309807.html
-- Ref: Electoral Commission NZ - Sainte-Laguë Formula Explained
-- https://www.electionresults.govt.nz/
DROP VIEW IF EXISTS parliament_seats;
CREATE VIEW parliament_seats AS
WITH RECURSIVE
party_totals AS (
    SELECT 
        p.party_displayName,
        p.partyId,
        SUM(v.votes) AS party_votes,
        SUM(v.votes) * 1.0 / (SELECT SUM(votes) FROM party_votes_rnz_preliminary) AS vote_ratio
    FROM party_votes_rnz_preliminary v
    JOIN parties_rnz p ON v.partyId = p.partyId
    GROUP BY p.partyId, p.party_displayName
),
-- Step 1: Filter parties meeting the 5% party vote threshold
-- (Note: If any party below 5% won an electorate seat, add: OR p.partyId IN (<electorate_winner_ids>))
qualifying_parties AS (
    SELECT *
    FROM party_totals
    WHERE vote_ratio >= 0.05
),
-- Step 2: Generate odd divisors (1, 3, 5, ..., 239) for up to 120 seats
odd_divisors(seat_num, divisor) AS (
    SELECT 1, 1
    UNION ALL
    SELECT seat_num + 1, divisor + 2
    FROM odd_divisors
    WHERE seat_num < 120
),
-- Step 3: Calculate Sainte-Laguë quotients and rank the top 120
ranked_quotients AS (
    SELECT 
        qp.partyId,
        qp.party_displayName,
        od.seat_num,
        (qp.party_votes * 1.0) / od.divisor AS quotient,
        ROW_NUMBER() OVER (ORDER BY (qp.party_votes * 1.0) / od.divisor DESC) AS quotient_rank
    FROM qualifying_parties qp
    CROSS JOIN odd_divisors od
)
-- Step 4: Count seats in the top 120 quotients for each party
SELECT
    pt.partyId,
    pt.party_displayName,
    pt.vote_ratio,
    COUNT(rq.quotient_rank) AS list_seats
FROM party_totals pt
LEFT JOIN ranked_quotients rq 
    ON pt.partyId = rq.partyId 
   AND rq.quotient_rank <= 120
GROUP BY pt.partyId, pt.party_displayName, pt.vote_ratio
ORDER BY list_seats DESC, pt.vote_ratio DESC;
