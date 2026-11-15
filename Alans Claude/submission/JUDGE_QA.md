# Judge questions and our answers

Finalists present for five minutes and then take questions. Agree who answers what. If we do not
know, we say: "We didn't get to test that, but here's how we would."

| Question | Our answer | Owner |
| --- | --- | --- |
| Isn't this just a wrapper around a translator? | The translator is a free pretrained model. What we built is the part that decides which of its outputs to trust: seven signals, a trained flagger, and a test against three baselines on data it never saw. | Builder |
| How do you know a translation is "bad"? | We compare it with a professional translation of the same sentence using chrF, and call the lowest quarter per language bad. That label is automatic and imperfect, so each of us rated a sample in our own language without seeing the flagger's score. | Builder |
| Why the lowest quarter per language, not one cut-off for all? | chrF is not comparable across scripts: Chinese scores sit on a different scale from Spanish. One cut-off would label almost all of one language bad for reasons unrelated to quality. | Builder |
| Does it beat a simple baseline? | Reviewing the 20% we flag catches [X]% of bad translations. Random catches 20%, longest-first [Y]%, translator confidence alone [Z]%. | Builder |
| The translator's confidence is already a good signal. What do you add? | [State the real gap.] The other signals catch what confidence misses, such as a confident translation with a changed number. If the gap is small, we say so. | Builder |
| Did anything leak from the test set? | The flagger, its length norms and the bad-translation cut-offs were all fitted on the dev split only. The devtest split was scored once. | Builder |
| Does it work for a language you didn't train on? | We trained on four languages and tested on the fifth, for each language. Result: [numbers]. [Kurmanji finding.] | Storyteller |
| Where does it fail? | Fluent sentences with the wrong meaning, and idioms translated word for word. The round trip can hide an error when the model makes the same mistake in both directions. Examples are in the app's failure gallery. | Storyteller |
| Why would an owner trust a flag? | Every flag gives its reason and shows the translation turned back into English, so someone who can't read the language can see the difference. A flag is a request to check, never a verdict. | Integrator |
| What happens when it misses a bad translation? | A wrong line gets published. That is why the app says "looks fine", not "correct", and why we warn that medical, legal and safety text always needs a qualified human. | Integrator |
| Why logistic regression and not a bigger model? | Every weight is readable, so each flag can be explained. With seven signals and a few thousand examples, a larger model would not have more to learn from. | Builder |
| Is it fair across languages? | We report every result per language. [Which language it serves worst, and by how much.] | Storyteller |
| Which parts did AI write, and do you understand them? | Claude helped plan, drafted the code and built the interface. We ran every experiment, rated the translations in our own languages, and can walk through each file. | Any of us |
| Who would actually use this? | A shop, school office or clinic that publishes in several languages and can afford to have only some lines checked. | Integrator |
