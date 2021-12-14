import z3


class Filter:
    nature_list = ["Hardy","Lonely","Brave","Adamant","Naughty","Bold","Docile","Relaxed","Impish","Lax","Timid","Hasty","Serious","Jolly","Naive","Modest","Mild","Quiet","Bashful","Rash","Calm","Gentle","Sassy","Careful","Quirky"]
    shiny_list = ["Star","Square","Star/Square"]

    def __init__(self,iv_min=None,iv_max=None,abilities=None,shininess=None,slot_min=None,slot_max=None,natures=None,marks=None,brilliant=None):
        self.iv_min = iv_min
        self.iv_max = iv_max
        self.abilities = abilities
        self.shininess = Filter.shiny_list.index(shininess) if shininess != None else None
        self.slot_min = slot_min
        self.slot_max = slot_max
        self.natures = [Filter.nature_list.index(nature) for nature in natures] if natures != None else None
        self.marks = marks
        self.brilliant = brilliant
    
    def compare_ivs(self,state):
        if self.iv_min != None:
            for i in range(6):
                if not self.iv_min[i] <= state.ivs[i] <= self.iv_max[i]:
                    return False
        return True
    
    def compare_brilliant(self,state):
        return state.brilliant or not self.brilliant
    
    def compare_fixed(self,state):
        if self.shininess == 0 and state.xor == 0:
            return False
        return self.compare_ivs(state)
    
    def compare_slot(self,state):
        return self.slot_min <= state.slot_rand <= self.slot_max if self.slot_min != None else True
    
    def compare_mark(self,state):
        return state.mark in self.marks if self.marks != None else True
    
    def compare_shiny(self,shiny):
        return shiny if self.shininess != None else True
    
    def compare_ability(self,state):
        return state.ability in self.abilities if self.abilities != None else True
    
    def compare_nature(self,state):
        return state.nature in self.natures if self.natures != None else True


class XOROSHIRO(object):
    ulongmask = 2 ** 64 - 1
    uintmask = 2 ** 32 - 1

    def __init__(self, seed, seed2 = 0x82A2B175229D6A5B):
            self.seed = [seed, seed2]

    @property
    def state(self):
        s0, s1 = self.seed
        return s0 | (s1 << 64)

    @staticmethod
    def rotl(x, k):
        return ((x << k) | (x >> (64 - k))) & XOROSHIRO.ulongmask

    def next(self):
        s0, s1 = self.seed
        result = (s0 + s1) & XOROSHIRO.ulongmask
        s1 ^= s0
        self.seed = [XOROSHIRO.rotl(s0, 24) ^ s1 ^ ((s1 << 16) & XOROSHIRO.ulongmask), XOROSHIRO.rotl(s1, 37)]
        return result

    def nextuint(self):
        return self.next() & XOROSHIRO.uintmask

    @staticmethod
    def getMask(x):
        x -= 1
        for i in range(6):
            x |= x >> (1 << i)
        return x
    
    def rand(self, N = uintmask):
        mask = XOROSHIRO.getMask(N)
        res = self.next() & mask
        while res >= N:
            res = self.next() & mask
        return res

    def quickrand1(self,mask): # 0~mask rand(mask + 1)
        return self.next() & mask

    def quickrand2(self,max,mask): # 0~max-1 rand(max)
        res = self.next() & mask
        while res >= max:
            res = self.next() & mask
        return res

    @staticmethod
    def find_seeds(ec,pid):
        solver = z3.Solver()
        start_s0 = z3.BitVecs('start_s0', 64)[0]

        sym_s0 = start_s0
        sym_s1 = 0x82A2B175229D6A5B

        # EC call
        result = ec
        sym_s0, sym_s1, condition = sym_xoroshiro128plus(sym_s0, sym_s1, result)
        solver.add(condition)

        # Blank call
        sym_s0, sym_s1 = sym_xoroshiro128plusadvance(sym_s0, sym_s1)

        # PID call
        result = pid
        sym_s0, sym_s1, condition = sym_xoroshiro128plus(sym_s0, sym_s1, result)
        solver.add(condition)
        
        models = get_models(solver)
        return [ model[start_s0].as_long() for model in models ]

class Xorshift:
    def __init__(self, state0, state1, state2, state3):
        self.seed = [state0,state1,state2,state3]
    
    @property
    def state(self):
        return (self.seed[3] << 96) | (self.seed[2] << 64) | (self.seed[1] << 32) | self.seed[0]

    def next(self):
        t = self.seed[0]
        s = self.seed[3]

        t ^= (t << 11) & 0xFFFFFFFF
        t ^= t >> 8
        t ^= s ^ (s >> 19)

        self.seed = self.seed[1:4] + [t]

        return ((t % 0xFFFFFFFF) + 0x80000000) & 0xFFFFFFFF
    
    def rand(self,mod=0x100000000):
        return self.next() % mod
    
    def __str__(self):
        return f"S[0]: {self.seed[0]:08X}  S[1]: {self.seed[1]:08X}  S[2]: {self.seed[2]:08X}  S[3]: {self.seed[3]:08X}"


class OverworldRNG:
    personality_marks = ["Rowdy","AbsentMinded","Jittery","Excited","Charismatic","Calmness","Intense","ZonedOut","Joyful","Angry","Smiley","Teary","Upbeat","Peeved","Intellectual","Ferocious","Crafty","Scowling","Kindly","Flustered","PumpedUp","ZeroEnergy","Prideful","Unsure","Humble","Thorny","Vigor","Slump"]
    
    def __init__(self,seed=0,tid=0,sid=0,shiny_charm=False,mark_charm=False,weather_active=False,is_fishing=False,is_static=False,forced_ability=False,flawless_ivs=0,is_shiny_locked=False,min_level=0,max_level=0,diff_held_item=False,filter=Filter(),egg_move_count=0,kos=0):
        self.rng = XOROSHIRO(seed & 0xFFFFFFFFFFFFFFFF, seed >> 64)
        self.advance = 0
        self.tid = tid
        self.sid = sid
        self.shiny_charm = shiny_charm
        self.mark_charm = mark_charm
        self.weather_active = weather_active
        self.is_fishing = is_fishing
        self.is_static = is_static
        self.forced_ability = forced_ability
        self.flawless_ivs = flawless_ivs
        self.is_shiny_locked = is_shiny_locked
        self.min_level = min_level
        self.max_level = max_level
        self.diff_held_item = diff_held_item
        self.egg_move_count = egg_move_count
        self.brilliant_thresh,self.brilliant_rolls = OverworldRNG.calculate_brilliant_info(kos)
        self.filter = filter
    
    @property
    def tsv(self):
        return self.tid ^ self.sid
        
    def advance_fast(self,advances):
        self.advance += advances
        for _ in range(advances):
            self.rng.next()

    def generate(self):
        state = self.generate_filter()
        self.rng.next()
        self.advance += 1
        return state

    def generate_filter(self):
        state = OverworldState()
        state.full_seed = self.rng.state
        state.advance = self.advance
        state.is_static = self.is_static
        state.hide_ability = self.forced_ability
        
        go = XOROSHIRO(*self.rng.seed.copy())
        if self.is_static:
            go.rand(100)
        else:
            if not self.is_fishing:
                go.rand()
            go.rand(100)
            go.rand(100)
            state.slot_rand = go.rand(100)
            if not self.filter.compare_slot(state):
                return
            if self.min_level != self.max_level:
                state.level = self.min_level + go.rand(self.max_level-self.min_level+1)
            else:
                state.level = self.min_level
            state.mark = OverworldRNG.rand_mark(go,self.weather_active,self.is_fishing,self.mark_charm)
            state.brilliant_rand = go.rand(1000)
            if state.brilliant_rand < self.brilliant_thresh:
                state.brilliant = True
            if not self.filter.compare_brilliant(state):
                return
        
        if not self.is_shiny_locked:
            for roll in range((3 if self.shiny_charm else 1) + (self.brilliant_rolls if state.brilliant else 0)):
                mock_pid = go.nextuint()
                shiny = (((mock_pid >> 16) ^ (mock_pid & 0xFFFF)) ^ self.tsv) < 16
                if shiny:
                    break
        else:
            shiny = False
        if not self.filter.compare_shiny(shiny):
            return
        go.rand(2)
        state.nature = go.rand(25)
        if not self.filter.compare_nature(state):
            return
        if not self.forced_ability:
            state.ability = 0 if go.rand(2) == 1 else 1
        else:
            state.ability = 0
        if not self.filter.compare_ability(state):
            return
        if not self.is_static and self.diff_held_item:
            go.rand(100)

        brilliant_ivs = 0
        if state.brilliant:
            brilliant_ivs = go.rand(2)|2
            if self.egg_move_count > 1:
                go.rand(self.egg_move_count)

        state.fixed_seed = go.nextuint()
        
        state.ec, state.pid, state.ivs = OverworldRNG.calculate_fixed(state.fixed_seed,self.tsv,shiny,self.flawless_ivs + brilliant_ivs)
        state.xor = (((state.pid >> 16) ^ (state.pid & 0xFFFF)) ^ self.tsv)
        if not self.filter.compare_fixed(state):
            return
        
        state.mark = OverworldRNG.rand_mark(go,self.weather_active,self.is_fishing,self.mark_charm)
        if not self.filter.compare_mark(state):
            return
        
        return state
    
    @staticmethod
    def calculate_brilliant_info(kos):
        if kos >= 500:
            return 30,6
        if kos >= 300:
            return 30,5
        if kos >= 200:
            return 30,4
        if kos >= 100:
            return 30,3
        if kos >= 50:
            return 25,2
        if kos >= 20:
            return 20,1
        if kos >= 1:
            return 15,1
        return 0,0

    @staticmethod
    def calculate_fixed(fixed_seed,tsv,shiny,forced_ivs):
        rng = XOROSHIRO(fixed_seed)
        ec = rng.nextuint()
        pid = rng.nextuint()
        if not shiny:
            if (((pid >> 16) ^ (pid & 0xFFFF)) ^ tsv) < 16:
                pid ^= 0x10000000
        else:
            if not (((pid >> 16) ^ (pid & 0xFFFF)) ^ tsv) < 16:
                pid = (((tsv ^ (pid & 0xFFFF)) << 16) | (pid & 0xFFFF)) & 0xFFFFFFFF

        ivs = [32]*6
        for i in range(forced_ivs):
            index = rng.rand(6)
            while ivs[index] != 32:
                index = rng.rand(6)
            ivs[index] = 31
        for i in range(6):
            if ivs[i] == 32:
                ivs[i] = rng.rand(32)

        return [ec,pid,ivs]
    
    @staticmethod
    def rand_mark(go,weather_active,is_fishing,mark_charm):
        for roll in range(3 if mark_charm else 1):
            rare_rand = go.rand(1000)
            personality_rand = go.rand(100)
            uncommon_rand = go.rand(50)
            weather_rand = go.rand(50)
            time_rand = go.rand(50)
            fish_rand = go.rand(25)
            
            if rare_rand == 0:
                return "Rare"
            if personality_rand == 0:
                return OverworldRNG.personality_marks[go.rand(len(OverworldRNG.personality_marks))]
            if uncommon_rand == 0:
                return "Uncommon"
            if weather_rand == 0:
                if weather_active:
                    return "Weather"
            if time_rand == 0:
                return "Time"
            if fish_rand == 0:
                if is_fishing:
                    return "Fishing"

    @staticmethod
    def calculateFromPKM(pkm):
        return OverworldRNG.calculate_fixed(pkm.seed,pkm.tid ^ pkm.sid,pkm.setShininess != 3,pkm.setIVs)


class BDSPStationaryGenerator:
    # TODO: filter/state usage
    def __init__(self,seed=0,tid=0,sid=0,flawless_ivs=0):
        self.rng = Xorshift(seed >> 96, (seed >> 64) & 0xFFFFFFFF, (seed >> 32) & 0xFFFFFFFF)
        self.tid = tid
        self.sid = sid
        self.flawless_ivs = flawless_ivs
        self.advance = 0
    
    def generate(self):
        go = Xorshift(*self.rng.seed.copy())
        ec = go.next()
        otid = go.next()
        pid = go.next()
        fake_xor = ((otid >> 16) ^ otid ^ (pid >> 16) ^ pid) & 0xFFFF
        real_xor = (self.sid ^ self.tid ^ (pid >> 16) ^ pid) & 0xFFFF

        if fake_xor < 16: # force shiny
            if fake_xor != real_xor:
                pid = pid & 0xFFFF | (self.tid ^ self.sid ^ pid ^ fake_xor != 0) << 0x10
        else: # anti-shiny
            if real_xor < 16:
                pid ^= 0x10000000
        real_xor = (self.sid ^ self.tid ^ (pid >> 16) ^ pid) & 0xFFFF

        ivs = [32]*6
        for i in range(self.flawless_ivs):
            index = go.rand(6)
            while ivs[index] != 32:
                index = go.rand(6)
            ivs[index] = 31
        
        for i in range(6):
            if ivs[i] == 32:
                ivs[i] = go.rand(32)

        ability = go.rand(1)
        nature = go.rand(25)

        self.rng.next()
        self.advance += 1

        return [self.advance-1,ec,pid,ivs,real_xor,ability,nature]

    @property
    def tsv(self):
        return self.tid ^ self.sid


class BDSPIDGenerator:
    # TODO: filter/state usage
    def __init__(self,seed=0):
        self.rng = Xorshift(seed >> 96, (seed >> 64) & 0xFFFFFFFF, (seed >> 32) & 0xFFFFFFFF)
    
    def generate(self):
        # main rng call because there is only 1 used
        sidtid = self.rng.next()
        tid = sidtid & 0xFFFF
        sid = sidtid >> 16
        tsv = sid^tid
        g8tid = sidtid % 1000000
        return [sidtid,tid,sid,g8tid,tsv]


class FrameGenerator(object):
    def print(self):
        from lookups import Util
        print(f"Seed: {self.seed:016X}    ShinyType: {self.ShinyType}    EC: {self.EC:08X}    PID: {self.PID:08X}")
        print(f"Ability: {self.Ability}    Gender: {Util.GenderSymbol[self.Gender]}    Nature: {Util.STRINGS.natures[self.Nature]}    IVs: {self.IVs}")


class Egg:
    EVERSTONE = 229
    DESTINYKNOT = 280
    POWERITEM = 289

    @staticmethod
    def getAbilityNum(baseAbility,randroll):
        if baseAbility == 4:
            if randroll < 20:
                return 1
            if randroll < 40:
                return 2
            return 'H'
        elif baseAbility == 1:
            return 1 if randroll < 80 else 2
        elif baseAbility == 2:
            return 1 if randroll < 20 else 2

    @staticmethod
    def getPowerItem(itemID):
        if Egg.POWERITEM <= itemID and itemID <= Egg.POWERITEM + 5:
            return itemID - Egg.POWERITEM
        return -1

    def __str__(self):
        from lookups import Util
        return (f"Seed: {self.seed:016X}    ShinyType: {self.ShinyType}    EC: {self.EC:08X}    PID: {self.PID:08X}\n" +
                f"Ability: {self.Ability}    Gender: {Util.GenderSymbol[self.Gender]}    Nature: {Util.STRINGS.natures[self.Nature]}    IVs: {self.IVs}")

    def __init__(self, seed, parent1, parent2, shinycharm, tid = 0, sid = 0):
        # slow generator
        self.seed = seed
        r = XOROSHIRO(seed)

        self.parents = [parent1.ec,parent2.ec]

        if parent1.gender == 0 or parent2.gender == 1 or (parent1.species == 132 and parent2.gender != 0):
            Male = parent1
            Female = parent2
        else:
            Female = parent1
            Male = parent2
        base = Male if Female.species == 132 else Female
        from lookups import Util
        parentpi = Util.PT.getFormeEntry(base.species,base.altForm)
        self.species = parentpi.BaseSpecies()

        self.NidoType = False
        if base.species in [29,32]:
            self.species = 29 if r.quickrand1(0x1) else 32
            self.NidoType = True
        if base.species in [313,314]:
            self.species = 314 if r.quickrand1(0x1) else 313
            self.NidoType = True
        if base.species == 490:
            self.species = 489
        self.forme = parentpi.BaseSpeciesForm()
        childpi = Util.PT.getFormeEntry(self.species,self.forme)
        self.GenderRatio = childpi.Gender()
        self.RandomGender = False
        if self.GenderRatio == 255:
            self.Gender = 2
        elif self.GenderRatio == 254:
            self.Gender = 1
        elif self.GenderRatio == 0:
            self.Gender = 0
        else:
            self.RandomGender = True
            self.Gender = 1 if r.quickrand2(252,0xFF) + 1 < self.GenderRatio else 0

        self.Nature = r.quickrand2(25,0x1F)
        self.BOTH_EVERSTONE = Male.helditem == Egg.EVERSTONE and Female.helditem == Egg.EVERSTONE
        self.FEMALE_STONE = Female.helditem == Egg.EVERSTONE
        self.HAS_STONE = Male.helditem == Egg.EVERSTONE or self.FEMALE_STONE
        if self.HAS_STONE:
            self.MALE_NATURE = Male.nature
            self.FEMALE_NATURE = Female.nature
            if self.BOTH_EVERSTONE:
                self.Nature = self.FEMALE_NATURE if r.quickrand1(0x1) else self.MALE_NATURE
            else :
                self.Nature = self.FEMALE_NATURE if self.FEMALE_STONE else self.MALE_NATURE

        self.baseAbility = base.abilityNum
        self.Ability = Egg.getAbilityNum(self.baseAbility, r.quickrand2(100,0x7F))

        self.InheritIVsCnt = 5 if Male.helditem == Egg.DESTINYKNOT or Female.helditem == Egg.DESTINYKNOT else 3

        self.InheritIVs = [-1, -1, -1, -1, -1, -1]
        self.FEMALE_POWER = Egg.getPowerItem(Female.helditem)
        self.MALE_POWER = Egg.getPowerItem(Male.helditem)
        self.BOTH_POWER = self.MALE_POWER >= 0 and self.FEMALE_POWER >= 0
        if self.BOTH_POWER:
            if r.quickrand1(0x1):
                self.InheritIVs[self.FEMALE_POWER] = 1
            else:
                self.InheritIVs[self.MALE_POWER] = 0
        elif self.MALE_POWER >= 0:
            self.InheritIVs[self.MALE_POWER] = 0
        elif self.FEMALE_POWER >= 0:
            self.InheritIVs[self.FEMALE_POWER] = 1
        if self.MALE_POWER >= 0 or self.FEMALE_POWER >= 0:
            self.InheritIVsCnt -= 1
            
        for ii in range(self.InheritIVsCnt):
            tmp = r.quickrand2(6,0x7)
            while self.InheritIVs[tmp] > -1:
                tmp = r.quickrand2(6,0x7)
            self.InheritIVs[tmp] = r.quickrand1(1)

        self.MaleIVs = Male.ivs
        self.FemaleIVs = Female.ivs
        self.IVs = [-1, -1, -1, -1, -1, -1]
        for j in range(6):
            self.IVs[j] = r.quickrand1(0x1F)
            if self.InheritIVs[j] == 0:
                self.IVs[j] = self.MaleIVs[j]
            elif self.InheritIVs[j] == 1:
                self.IVs[j] = self.FemaleIVs[j]

        self.EC = r.nextuint()

        self.txor = tid ^ sid
        self.ShinyType = 0
        reroll = 6 if Male.language != Female.language else 0
        self.ShinyCharm = shinycharm
        if shinycharm:
            reroll += 2
        self.PID_REROLL = reroll
        for ii in range(self.PID_REROLL):
            self.PID = r.nextuint()
            self.XOR = (self.PID >> 16) ^ (self.PID & 0xFFFF) ^ self.txor
            if self.XOR < 16:
                self.ShinyType = 1 if self.XOR else 2
                break

        self.ball = base.ball
        self.RandBall = False
        if Male.species == Female.species:
            self.RandBall = True
            self.BASE_BALL = base.ball
            self.MALE_BALL = Male.ball
            if r.quickrand2(100,0x7F) >= 50:
                self.ball =  self.MALE_BALL
        if self.ball == 16 or self.ball == 1:
            self.ball = 4

    def reseed(self, seed):
        # Asssume that parents doesn't change. Quick version
        self.seed = seed
        r = XOROSHIRO(seed)

        if self.NidoType:
            if self.species in [29,32]:
                self.species = 29 if r.quickrand1(0x1) else 32
            if self.species in [313,314]:
                self.species = 314 if r.quickrand1(0x1) else 313
        if self.RandomGender:
            self.Gender = 1 if r.quickrand2(252,0xFF) + 1 < self.GenderRatio else 0

        self.Nature = r.quickrand2(25,0x1F)
        if self.HAS_STONE:
            if self.BOTH_EVERSTONE:
                self.Nature = self.FEMALE_NATURE if r.quickrand1(0x1) else self.MALE_NATURE
            else:
                self.Nature = self.FEMALE_NATURE if self.FEMALE_STONE else self.MALE_NATURE

        self.Ability = Egg.getAbilityNum(self.baseAbility, r.quickrand2(100,0x7F))

        self.InheritIVs = [-1, -1, -1, -1, -1, -1]
        if self.BOTH_POWER:
            if r.quickrand1(0x1):
                self.InheritIVs[self.FEMALE_POWER] = 1
            else:
                self.InheritIVs[self.MALE_POWER] = 0
        elif self.MALE_POWER >= 0:
            self.InheritIVs[self.MALE_POWER] = 0
        elif self.FEMALE_POWER >= 0:
            self.InheritIVs[self.FEMALE_POWER] = 1

        for ii in range(self.InheritIVsCnt):
            tmp = r.quickrand2(6,0x7)
            while self.InheritIVs[tmp] > -1:
                tmp = r.quickrand2(6,0x7)
            self.InheritIVs[tmp] = r.quickrand1(1)

        self.IVs = [-1, -1, -1, -1, -1, -1]
        for j in range(6):
            self.IVs[j] = r.quickrand1(0x1F)
            if self.InheritIVs[j] == 0:
                self.IVs[j] = self.MaleIVs[j]
            elif self.InheritIVs[j] == 1:
                self.IVs[j] = self.FemaleIVs[j]

        self.EC = r.nextuint()

        for ii in range(self.PID_REROLL):
            self.PID = r.nextuint()
            self.XOR = (self.PID >> 16) ^ (self.PID & 0xFFFF) ^ self.txor
            if self.XOR < 16:
                self.ShinyType = 1 if self.XOR else 2
                break

        if self.RandBall:
            self.ball = self.MALE_BALL if r.quickrand2(100,0x7F) >= 50 else self.BASE_BALL
            if self.ball == 16 or self.ball == 1:
                self.ball = 4

class Raid(FrameGenerator):
    toxtricityAmpedNatures = [3, 4, 2, 8, 9, 19, 22, 11, 13, 14, 0, 6, 24]
    toxtricityLowKeyNatures = [1, 5, 7, 10, 12, 15, 16, 17, 18, 20, 21, 23]

    def __init__(self, seed, TID, SID, flawlessiv, shinyLock = 0, ability = 4, gender = 0, species = 25, altform = 0):
        from lookups import Util
        pi = Util.PT.getFormeEntry(species,altform)
        self.seed = seed
        r = XOROSHIRO(seed)
        self.EC = r.nextuint()
        OTID = r.nextuint()
        self.PID = r.nextuint()
        PSV = self.getShinyValue(self.PID)
        PIDShinyType = self.getShinyXor(self.PID) ^ TID ^ SID
        TSV = self.getShinyValue(TID ^ SID)

        if shinyLock == 0: # random shiny chance
            SeedShinyType = self.getShinyType(self.PID,OTID)
            FTSV = self.getShinyValue(OTID)
            if FTSV == PSV: # force shiny
                if SeedShinyType == 1:
                    self.ShinyType = 'Star'
                    if PSV != TSV or not PIDShinyType: # force to star if PID isn't shiny/is shiny square
                        self.PID = Raid.getFinalPID(self.PID,TID,SID,SeedShinyType)
                elif SeedShinyType == 2:
                    self.ShinyType = 'Square'
                    if PSV != TSV or PIDShinyType: # force to square if PID isn't shiny/is shiny star
                        self.PID = Raid.getFinalPID(self.PID,TID,SID,SeedShinyType)
            else: # force non-shiny
                self.ShinyType = 'None'
                if PSV == TSV:
                    self.PID ^= 0x10000000
        elif shinyLock == 1: # forced non-shiny chance
            self.ShinyType = 'None'
            if PSV == TSV:
                self.PID ^= 0x10000000
        else: # forced shiny chance
            if PIDShinyType >= 16 or PIDShinyType: # force to square if PID isn't shiny/is shiny star
                self.PID = Raid.getFinalPID(self.PID,TID,SID,2)
            self.ShinyType = 'Square'

        i = 0
        self.IVs = [0,0,0,0,0,0]
        while i < flawlessiv:
            stat = r.quickrand2(6,0x7)
            if self.IVs[stat] == 0:
                self.IVs[stat] = 31
                i += 1
        for i in range(6):
            if self.IVs[i] == 0:
                self.IVs[i] = r.quickrand1(0x1F)

        if ability == 4:
            self.Ability = r.quickrand2(3,3) + 1
        elif ability == 3:
            self.Ability = r.quickrand1(0x1) + 1
        else:
            self.Ability = ability + 1
        if self.Ability == 3:
            self.Ability = 'H'

        if gender == 0:
            ratio = pi.Gender()
            if ratio == 255:
                self.Gender = 2
            elif ratio == 254:
                self.Gender = 1
            elif ratio == 0:
                self.Gender = 0
            else:
                self.Gender = 1 if r.quickrand2(253,0xFF) + 1 < ratio else 0
        else:
            self.Gender = gender - 1

        if species != 849:
            self.Nature = r.quickrand2(25,0x1F)
        elif altform == 0:
            self.Nature = Raid.toxtricityAmpedNatures[r.quickrand2(13,0xF)]
        else:
            self.Nature = Raid.toxtricityLowKeyNatures[r.quickrand2(12,0xF)]

    @staticmethod
    def getShinyXor(val):
        return (val >> 16) ^ (val & 0xFFFF)

    @staticmethod
    def getShinyValue(PID):
        return Raid.getShinyXor(PID) >> 4

    @staticmethod
    def getShinyType(PID,OTID):
        p = Raid.getShinyXor(PID)
        t = Raid.getShinyXor(OTID)
        if p == t:
            return 2 # Square
        if p ^ t < 16:
            return 1 # Star
        return 0

    @staticmethod
    def getFinalPID(PID,TID,SID,SeedShinyType):
        highPID = (PID & 0xFFFF) ^ TID ^ SID ^ (2 - SeedShinyType)
        return (highPID << 16) | (PID & 0xFFFF)

    @staticmethod
    def getNextShinyFrame(seed):
        for ii in range(99999):
            r = XOROSHIRO(seed)
            seed = r.next()
            OTID = r.nextuint()
            PID = r.nextuint()
            shinyType = Raid.getShinyType(PID, OTID)
            if shinyType != 0:
                return ii

    @staticmethod
    def getseeds(EC,PID,IVs):
        result = []
        seeds = XOROSHIRO.find_seeds(EC, PID)    
        if len(seeds) > 0:
            for iv_count in range(IVs.count(31) + 1):
                for seed in seeds:
                    r = Raid(seed,0,0,iv_count)
                    if IVs == r.IVs:
                        result.append([seed,iv_count])

        if len(result) > 0:
            return result

        seedsXor = XOROSHIRO.find_seeds(EC, PID ^ 0x10000000) # Check for shiny lock
        if len(seedsXor) > 0:
            for iv_count in range(IVs.count(31) + 1):
                for seed in seeds:
                    r = Raid(seed,iv_count)
                    if IVs == r.IVs:
                        result.append([seed,-iv_count])
        return result
        

class OverworldState:
    natures = ["Hardy","Lonely","Brave","Adamant","Naughty","Bold","Docile","Relaxed","Impish","Lax","Timid","Hasty","Serious","Jolly","Naive","Modest","Mild","Quiet","Bashful","Rash","Calm","Gentle","Sassy","Careful","Quirky"]
    genders = ['♂','♀','-']

    def __init__(self):
        self.advance = 0
        self.full_seed = 0
        self.fixed_seed = 0
        self.is_static = True
        self.mark = None
        self.brilliant = False
        self.hide_ability = False
        self.slot_rand = 100
        self.level = 0
        self.nature = 0
        self.ability = 0
        self.ec = 0
        self.pid = 0
        self.xor = 0
        self.ivs = [32]*6
        self.gender = 2
        
    def __str__(self):
        if self.is_static:
            return f"{self.advance} {self.ec:08X} {self.pid:08X} {'No' if self.xor >= 16 else ('Square' if self.xor == 0 else 'Star')} {self.natures[self.nature]} {self.ability} {self.genders[self.gender]} {'/'.join(str(iv) for iv in self.ivs)} {self.mark}"
        else:
            return f"{self.advance} {self.level} {self.slot_rand} {'Brilliant! ' if self.brilliant else ''}{self.ec:08X} {self.pid:08X} {'No' if self.xor >= 16 else ('Square' if self.xor == 0 else 'Star')} {self.natures[self.nature]} {str(self.ability)+' ' if not self.hide_ability else ''}{self.genders[self.gender]} {'/'.join(str(iv) for iv in self.ivs)} {self.mark}"


def sym_xoroshiro128plus(sym_s0, sym_s1, result):
    sym_r = (sym_s0 + sym_s1) & 0xFFFFFFFFFFFFFFFF  
    condition = (sym_r & 0xFFFFFFFF) == result

    sym_s0, sym_s1 = sym_xoroshiro128plusadvance(sym_s0, sym_s1)

    return sym_s0, sym_s1, condition

def sym_xoroshiro128plusadvance(sym_s0, sym_s1):
    s0 = sym_s0
    s1 = sym_s1
    
    s1 ^= s0
    sym_s0 = z3.RotateLeft(s0, 24) ^ s1 ^ (s1 << 16)
    sym_s1 = z3.RotateLeft(s1, 37)

    return sym_s0, sym_s1

def get_models(s):
    result = []
    while s.check() == z3.sat:
        m = s.model()
        result.append(m)
        
        # Constraint that makes current answer invalid
        d = m[0]
        c = d()
        s.add(c != m[d])

    return result
