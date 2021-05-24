from random import choice

def generate_bs():
    verbs = ['aggregate', 'architect', 'benchmark', 'brand', 'cultivate', 'deliver', 'deploy', 'disintermediate', 'drive', 'e-enable', 'embrace', 'empower', 'enable', 'engage', 'engineer', 'enhance', 'envision', 'envisioneer', 'evolve', 'expedite', 'exploit', 'extend', 'facilitate', 'generate', 'grow', 'harness', 'implement', 'incentivize', 'incubate', 'innovate', 'integrate', 'impact', 'iterate', 'leverage', 'matrix', 'maximize', 'mesh', 'monetize', 'morph', 'optimize', 'orchestrate', 'productize', 'recontextualize', 'redefine', 'reintermediate', 'reinvent', 'repurpose', 'revolutionize', 'scale', 'seize', 'strategize', 'streamline', 'syndicate', 'synergize', 'synthesize', 'target', 'transform', 'transition', 'unleash', 'utilize', 'visualize', 'whiteboard']

    adjectives = ['24/365', '24/7', 'B2B', 'B2C', 'back-end', 'best-of-breed', 'bleeding-edge', 'blockchain', 'bricks-and-clicks', 'clicks-and-mortar', 'cloud', 'collaborative', 'compelling', 'cross-platform', 'cross-media', 'customized', 'cutting-edge', 'distributed', 'dot-com', 'down stream', 'dynamic', 'e-business', 'efficient', 'end-to-end', 'enterprise', 'extensible', 'frictionless', 'front-end', 'global', 'granular', 'holistic', 'impactful', 'innovative', 'integrated', 'interactive', 'intuitive', 'killer', 'leading-edge', 'magnetic', 'mission-critical', 'next-generation', 'one-to-one', 'open-source', 'out-of-the-box', 'plug-and-play', 'proactive', 'real-time', 'revolutionary', 'rich', 'robust', 'scalable', 'seamless', 'sexy', 'sticky', 'strategic', 'synergistic', 'transparent', 'turn-key', 'ubiquitous', 'user-centric', 'upstream', 'value-added', 'venture', 'vertical', 'viral', 'virtual', 'visionary', 'web-enabled', 'wireless', 'world-class']

    nouns = ['action-items', 'ai', 'applications', 'architectures', 'bandwidth', 'channels', 'communities', 'content', 'convergence', 'dark web', 'deliverables', 'e-business', 'e-commerce', 'e-markets', 'e-services', 'e-tailers', 'experiences', 'eyeballs', 'functionalities', 'infomediaries', 'infrastructures', 'initiatives', 'interfaces', 'machine learning', 'markets', 'methodologies', 'metrics', 'mindshare', 'models', 'networks', 'niches', 'paradigms', 'partnerships', 'platforms', 'portals', 'relationships', 'ROI', 'SaaS', 'start ups', 'synergies', 'web-readiness', 'schemas', 'solutions', 'supply-chains', 'systems', 'technologies', 'users', 'vortals', 'web services']

    verb, adjective, noun = 'bullshit', 'bullshit', 'bullshit'


    while noun in adjective or verb in adjective or adjective in noun or verb in noun or adjective in verb or noun in verb:
        verb = choice(verbs)
        adjective = choice(adjectives)
        noun = choice(nouns)
    
        
    bullshit = verb + ' ' + adjective + ' ' + noun
    
    return bullshit

if __name__ == '__main__':
    print(generate_bs())