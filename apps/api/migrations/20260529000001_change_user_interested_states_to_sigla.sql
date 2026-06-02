-- Migration: 20260529000001_change_user_interested_states_to_sigla
-- Description: Altera semântica de user_interested_states.state_id para armazenar
--              a sigla da UF (ex: "PE") em vez do ID numérico do IBGE (ex: "26").
--              A coluna já é VARCHAR(2), não há mudança de tipo.
--              As opportunities usam location_state = sigla, então o filtro
--              .in_("location_state", state_ids) agora funciona corretamente.

-- Mapeamento IBGE ID → sigla para conversão de dados existentes
-- (todos os 26 estados + DF)
UPDATE user_interested_states SET state_id = 'RO' WHERE state_id = '11';
UPDATE user_interested_states SET state_id = 'AC' WHERE state_id = '12';
UPDATE user_interested_states SET state_id = 'AM' WHERE state_id = '13';
UPDATE user_interested_states SET state_id = 'RR' WHERE state_id = '14';
UPDATE user_interested_states SET state_id = 'PA' WHERE state_id = '15';
UPDATE user_interested_states SET state_id = 'AP' WHERE state_id = '16';
UPDATE user_interested_states SET state_id = 'TO' WHERE state_id = '17';
UPDATE user_interested_states SET state_id = 'MA' WHERE state_id = '21';
UPDATE user_interested_states SET state_id = 'PI' WHERE state_id = '22';
UPDATE user_interested_states SET state_id = 'CE' WHERE state_id = '23';
UPDATE user_interested_states SET state_id = 'RN' WHERE state_id = '24';
UPDATE user_interested_states SET state_id = 'PB' WHERE state_id = '25';
UPDATE user_interested_states SET state_id = 'PE' WHERE state_id = '26';
UPDATE user_interested_states SET state_id = 'AL' WHERE state_id = '27';
UPDATE user_interested_states SET state_id = 'SE' WHERE state_id = '28';
UPDATE user_interested_states SET state_id = 'BA' WHERE state_id = '29';
UPDATE user_interested_states SET state_id = 'MG' WHERE state_id = '31';
UPDATE user_interested_states SET state_id = 'ES' WHERE state_id = '32';
UPDATE user_interested_states SET state_id = 'RJ' WHERE state_id = '33';
UPDATE user_interested_states SET state_id = 'SP' WHERE state_id = '35';
UPDATE user_interested_states SET state_id = 'PR' WHERE state_id = '41';
UPDATE user_interested_states SET state_id = 'SC' WHERE state_id = '42';
UPDATE user_interested_states SET state_id = 'RS' WHERE state_id = '43';
UPDATE user_interested_states SET state_id = 'MS' WHERE state_id = '50';
UPDATE user_interested_states SET state_id = 'MT' WHERE state_id = '51';
UPDATE user_interested_states SET state_id = 'GO' WHERE state_id = '52';
UPDATE user_interested_states SET state_id = 'DF' WHERE state_id = '53';

COMMENT ON COLUMN user_interested_states.state_id
    IS 'Sigla da UF (ex: "PE", "SP") — alinhado com opportunities.location_state';
