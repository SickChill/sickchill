describe('metaToBool', function(){
    it('should return true', function(){
        chai.assert.equal(true, metaToBool('FAKE_TRUE_BOOLEAN'));
        chai.assert.equal(true, metaToBool('FAKE_TRUE_NUMBER'));
    });
    it('should return false', function(){
        chai.assert.equal(false, metaToBool('FAKE_FALSE_BOOLEAN'));
        chai.assert.equal(false, metaToBool('FAKE_FALSE_NUMBER'));
    });
    it('should return undefined', function(){
        chai.assert.equal(undefined, metaToBool('FAKE_UNDEFINED'));
    });
});
describe('getMeta', function(){
    it('should return meta variable', function(){
        chai.assert.equal('RANDOM_CONTENT', getMeta('FAKE_CONTENT'));
    });
});
describe('isMeta', function(){
    it('should return true if any string in array is matched', function(){
        chai.assert.equal(true, isMeta('FAKE_CONTENT', ['RANDOM_CONTENT']));
    });
    it('should return false if no strings in the array match', function(){
        chai.assert.equal(false, isMeta('FAKE_CONTENT', ['a', 'b', 'c']));
    });
});
describe('shiftReturn', function(){
    it('should return an array without the first item', function(){
        chai.assert.deepEqual(['2', '3'], shiftReturn(['1', '2', '3']));
    });
    it('should return an empty array', function(){
        chai.assert.deepEqual([], shiftReturn(['1']));
    });
});
